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
        print("No Bitwarden JSON found next to the executable.")
        sys.exit(1)

    out_path = base / "keeperimportfile.json"
    count = convert_bitwarden_to_keeper_json(src, out_path)
    print(f"Converted {count} record(s) → {out_path}")


if __name__ == "__main__":
    main()


