import json
import re
import urllib.request
import urllib.error

INPUT_FILE = "payloads.json"
OUTPUT_FILE = "payloads.json"

PAYLOAD_CONFIGS = [
    {
        "name": "Direct Package Installer (PKG Sender)",
        "repo": "Loopayeh/pkg-sender",
        "asset_pattern": r"^pkg-receiver.*\.elf$",
        "include_prereleases": False
    },
    {
        "name": "ShadowMountPlus (Pre-Release)",
        "repo": "drakmor/ShadowMountPlus",
        "asset_pattern": r"^shadowmountplus.*\.elf$",
        "include_prereleases": True
    },
    {
        "name": "KFStuff-Lite (Drakmor)",
        "repo": "drakmor/kstuff-lite",
        "asset_pattern": r"^(kfstuff|kstuff).*\.elf$",
        "include_prereleases": True
    },
    {
        "name": "Pegasus DL",
        "repo": "pegasus-ps5/pegasus-dl",
        "asset_pattern": r"^pegasus_dl.*\.elf$",
        "include_prereleases": False
    },
    {
        "name": "Apr-emu-updater",
        "repo": "tsuramatsu1/apr-emu-updater",
        "asset_pattern": r"^apr_emu_updater.*\.elf$",
        "include_prereleases": False
    },
    {
        "name": "LegacyJB",
        "repo": "Phoenixx1202/LegacyJB",
        "asset_pattern": r"^LegacyJB.*\.elf$",
        "include_prereleases": False
    }
]

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
    """
    Inserta la versión en el nombre del archivo si este no la contiene.
    Ejemplo: 'shadowmountplus.elf' + '1.7beta3' -> 'shadowmountplus-1.7beta3.elf'
    """
    clean_tag = tag_name.lstrip('v')  # Elimina la 'v' inicial si está presente
    if clean_tag.lower() in original_name.lower():
        return original_name
    
    if original_name.lower().endswith('.elf'):
        base = original_name[:-4]
        return f"{base}-{clean_tag}.elf"
    
    return f"{original_name}-{clean_tag}"

def update_payloads():
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró el archivo {INPUT_FILE}")
        return

    payloads = data.get("payloads", [])

    for config in PAYLOAD_CONFIGS:
        target_name = config["name"]
        repo = config["repo"]
        pattern = re.compile(config["asset_pattern"], re.IGNORECASE)
        include_prereleases = config.get("include_prereleases", False)
        is_raw = config.get("is_raw", False)

        print(f"\n--- Buscando actualizaciones para: {target_name} ({repo}) ---")
        release = get_latest_release(repo, include_prereleases)

        if not release:
            print(f"[ADVERTENCIA] No se obtuvieron lanzamientos para {repo}. Se omite.")
            continue

        tag_name = release.get("tag_name", "")
        assets = release.get("assets", [])

        matching_asset = None
        for asset in assets:
            if pattern.search(asset["name"]):
                matching_asset = asset
                break

        for payload in payloads:
            if payload.get("name") == target_name:
                updated = False
                
                if matching_asset:
                    raw_filename = matching_asset["name"]
                    versioned_filename = make_versioned_filename(raw_filename, tag_name)

                    download_url = matching_asset["browser_download_url"]
                    if is_raw:
                        download_url = f"https://raw.githubusercontent.com/{repo}/{tag_name}/{raw_filename}"

                    if payload.get("url") != download_url:
                        print(f"  URL actualizada: {payload.get('url')} -> {download_url}")
                        payload["url"] = download_url
                        updated = True

                    if payload.get("filename") != versioned_filename:
                        print(f"  Filename actualizado: {payload.get('filename')} -> {versioned_filename}")
                        payload["filename"] = versioned_filename
                        updated = True

                if tag_name and payload.get("version") != tag_name:
                    print(f"  Versión actualizada: {payload.get('version')} -> {tag_name}")
                    payload["version"] = tag_name
                    updated = True

                if not updated:
                    print("  Ya se encuentra en la versión más reciente.")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("\n¡Proceso de actualización completado!")

if __name__ == "__main__":
    update_payloads()
