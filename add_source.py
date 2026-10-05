import json
import re
import sys
import urllib.request

def extraer_repo(url_o_repo):
    # Extrae 'usuario/repositorio' aunque pegues la URL completa de GitHub
    match = re.search(r"github\.com/([^/]+/[^/]+)", url_o_repo)
    if match:
        return match.group(1).rstrip(".git")
    return url_o_repo.strip()

def agregar_fuente(repo_input, category_input="Utilities"):
    repo_path = extraer_repo(repo_input)
    
    # Consultar API de GitHub para obtener datos del repositorio
    api_url = f"https://api.github.com/repos/{repo_path}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "PS5-Payload-Updater/1.0"})
    
    try:
        with urllib.request.urlopen(req) as response:
            repo_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error al consultar el repositorio {repo_path}: {e}")
        return

    name = repo_data.get("name", repo_path.split("/")[-1])
    description = repo_data.get("description") or "Payload para PS5"

    nueva_entrada = {
        "name": name,
        "repo": repo_path,
        "asset_pattern": r".*\.elf$",
        "category": category_input,
        "description": description
    }

    # Leer sources.json existente
    try:
        with open("sources.json", "r", encoding="utf-8") as f:
            sources = json.load(f)
    except FileNotFoundError:
        sources = []

    # Verificar si ya existe para no duplicar
    if any(s.get("repo").lower() == repo_path.lower() for s in sources):
        print(f"El repositorio {repo_path} ya existe en sources.json.")
        return

    sources.append(nueva_entrada)

    # Guardar sources.json
    with open("sources.json", "w", encoding="utf-8") as f:
        json.dump(sources, f, indent=2, ensure_ascii=False)

    print(f"¡Agregado exitosamente {name} ({repo_path}) a sources.json!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url_input = sys.argv[1]
        cat_input = sys.argv[2] if len(sys.argv) > 2 else "Utilities"
        agregar_fuente(url_input, cat_input)
