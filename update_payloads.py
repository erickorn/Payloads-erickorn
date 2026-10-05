import json
import re
import urllib.request
import urllib.error

SOURCES_FILE = "sources.json"
OUTPUT_FILE = "payloads.json"
REPO_TITLE = "Mi Repositorio PS5 Custom"

def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PS5-Payload-Updater/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"[ERROR] HTTP Error {e.code} al consultar {url}")
        return None
    except Exception as e:
        print(f"[ERROR] Error inesperado al consultar {url}: {e}")
        return None

def get_latest_release(repo_path, include_prereleases=False):
    if include_prereleases:
        url = f"https://api.github.com/repos/{repo_path}/releases"
        releases = fetch_json(url)
        if releases and isinstance(releases, list) and len(releases) > 0:
            return releases[0]
        return None
    else:
        url = f"https://api.github.com/repos/{repo_path}/releases/latest"
        return fetch_json(url)

def make_versioned_filename(original_name, tag_name):
    clean_tag = tag_name.lstrip('v')
    if clean_tag.lower() in original_name.lower():
        return original_name
    
    if original_name.lower().endswith('.elf'):
        base = original_name[:-4]
        return f"{base}-{clean_tag}.elf"
    
    return f"{original_name}-{clean_tag}"

def update_payloads():
    try:
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            sources = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo de fuentes {SOURCES_FILE}")
        return

    updated_payloads = []

    for item in sources:
        target_name = item.get("name")
        repo = item.get("repo")
        pattern_str = item.get("asset_pattern", r".*\.elf$")
        pattern = re.compile(pattern_str, re.IGNORECASE)
        include_prereleases = item.get("include_prereleases", False)
        is_raw = item.get("is_raw", False)
        category = item.get("category", "General")
        description = item.get("description", "Payload para PS5")

        print(f"\n--- Procesando: {target_name} ({repo}) ---")
        release = get_latest_release(repo, include_prereleases)

        if not release:
            print(f"[ADVERTENCIA] No se obtuvieron datos para {repo}. Se omite.")
            continue

        tag_name = release.get("tag_name", "v1.0")
        assets = release.get("assets", [])

        matching_asset = None
        for asset in assets:
            if pattern.search(asset["name"]):
                matching_asset = asset
                break

        if matching_asset:
            raw_filename = matching_asset["name"]
            versioned_filename = make_versioned_filename(raw_filename, tag_name)

            download_url = matching_asset["browser_download_url"]
            if is_raw:
                download_url = f"https://raw.githubusercontent.com/{repo}/{tag_name}/{raw_filename}"

            payload_entry = {
                "name": target_name,
                "filename": versioned_filename,
                "url": download_url,
                "description": description,
                "version": tag_name,
                "category": category
            }
            updated_payloads.append(payload_entry)
            print(f"  [OK] Agregado/Actualizado: {versioned_filename} ({tag_name})")
        else:
            print(f"[ADVERTENCIA] No se encontró un archivo .elf compatible en {repo}.")

    output_data = {
        "name": REPO_TITLE,
        "payloads": updated_payloads
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\n¡Catálogo payloads.json generado y actualizado con éxito!")

if __name__ == "__main__":
    update_payloads()
