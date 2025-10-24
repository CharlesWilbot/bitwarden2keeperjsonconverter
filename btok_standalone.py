import json
import sys
from pathlib import Path
from typing import Optional

# Reuse the converter implementation
from convert_bw_json_to_keeper_json import convert_bitwarden_to_keeper_json


def find_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def looks_like_bitwarden_json(path: Path) -> bool:
    try:
        with path.open("r", encoding="utf-8") as h:
            data = json.load(h)
        return isinstance(data, dict) and "items" in data
    except Exception:
        return False


def pick_source_json(base_dir: Path) -> Optional[Path]:
    # Choose the newest .json that isn't the output file name
    candidates = [
        p for p in base_dir.glob("*.json")
        if p.name.lower() not in {"keeperimportfile.json", "keeper_import.json"}
    ]
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for p in candidates:
        if looks_like_bitwarden_json(p):
            return p
    return None


def main() -> None:
    base = find_base_dir()
    src = pick_source_json(base)
    if not src:
        print("L'utilitaire de conversion n'a pas trouvé le fichier Bitwarden (vaultwarden) à convertir. Assurez vous que le fichier JSON est dans le même dossier que cet utilitaire.")
        input("\nAppuyez sur Entrée pour fermer...")
        return

    out_path = base / "keeperimportfile.json"
    count = convert_bitwarden_to_keeper_json(src, out_path)
    print(f"Votre voute Bitwarden (vaultwarden) a été convertie et le fichier keeperimportfile.json sera le fichier à importer dans Keepersecurity.ca")
    print(f"\n{count} entrées ont été converties dans le processus.")
    print("\nPrenez note que les fichiers joints doivent être importés manuellement par la suite.")
    input("\nAppuyez sur Entrée pour fermer...")


if __name__ == "__main__":
    main()




