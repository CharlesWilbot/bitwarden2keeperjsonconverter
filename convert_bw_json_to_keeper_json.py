import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


SOURCE_DIR = Path("source")
TARGET_DIR = Path("target")
DEFAULT_OUTPUT = TARGET_DIR / "keeper_import.json"


def load_latest_source_json(source_dir: Path) -> Path:
    candidates = sorted(source_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No JSON files found in {source_dir}")
    return candidates[0]


def parse_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_id_to_name_map(data: Dict[str, Any]) -> Dict[str, str]:
    id_to_name: Dict[str, str] = {}
    for c in data.get("collections", []) or []:
        cid = c.get("id")
        name = c.get("name") or ""
        if cid:
            id_to_name[cid] = name
    for f in data.get("folders", []) or []:
        fid = f.get("id")
        name = f.get("name") or ""
        if fid and fid not in id_to_name:
            id_to_name[fid] = name
    return id_to_name


def normalize_url(url: str) -> str:
    if not url:
        return ""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        return url
    # If URL seems like hostname/path without scheme, prefix https://
    return f"https://{url}"


def extract_first_uri(login_obj: Dict[str, Any]) -> str:
    uris = login_obj.get("uris") or []
    for entry in uris:
        if isinstance(entry, dict) and entry.get("uri"):
            return normalize_url(str(entry["uri"]))
        if isinstance(entry, str) and entry:
            return normalize_url(entry)
    return ""


def hostname_from_url(url: str) -> Optional[str]:
    m = re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://([^/]+)", url)
    if m:
        return m.group(1)
    return None


def build_totp_otpauth(secret: str, title: str, username: str, login_url: str) -> str:
    # Build a reasonable otpauth URL for Keeper's $oneTimeCode field
    issuer = hostname_from_url(login_url) or "Imported"
    account = username or title or issuer
    label = f"{issuer}:{account}"
    # Keeper sample includes algorithm, digits, period defaults
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"
    )


def map_custom_fields(bitwarden_fields: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if not isinstance(bitwarden_fields, list):
        return result
    suffix = ":1"  # Follow the sample's key style
    for field in bitwarden_fields:
        if not isinstance(field, dict):
            continue
        name = str(field.get("name") or field.get("type") or "field")
        value = field.get("value")
        if value is None:
            continue
        ftype = field.get("type")  # 0=text, 1=hidden
        if ftype == 1:
            key = f"$secret:{name}{suffix}"
        else:
            key = f"$text:{name}{suffix}"
        result[key] = value
    return result


def to_keeper_folder_path(name: str) -> str:
    # Keeper expects folder hierarchy separated by backslashes
    return (name or "").replace("/", "\\")


def bw_item_to_keeper_record(item: Dict[str, Any], id_to_name: Dict[str, str]) -> Dict[str, Any]:
    title = item.get("name") or ""
    notes = item.get("notes") or ""
    bw_type = item.get("type")  # 1=login, 2=secure note, 3=card, 4=identity
    keeper_type = "login" if bw_type == 1 else "note"

    login_obj: Dict[str, Any] = item.get("login") or {}
    login = login_obj.get("username") or ""
    password = login_obj.get("password") or ""
    login_url = extract_first_uri(login_obj)

    # Build custom fields
    custom_fields = map_custom_fields(item.get("fields"))

    # TOTP -> $oneTimeCode otpauth
    totp_secret = (login_obj.get("totp") or "").strip()
    if totp_secret:
        custom_fields["$oneTimeCode::1"] = build_totp_otpauth(totp_secret, title, login, login_url)

    # Map folders
    folders: List[Dict[str, str]] = []
    folder_name = None
    # Prefer folderId for personal exports
    folder_id = item.get("folderId")
    if folder_id:
        folder_name = id_to_name.get(folder_id)
    # If not found, try first collection as a folder hint
    if not folder_name:
        col_ids = item.get("collectionIds") or []
        if isinstance(col_ids, list) and col_ids:
            folder_name = id_to_name.get(col_ids[0])
    if folder_name:
        folders.append({"folder": to_keeper_folder_path(folder_name)})

    record: Dict[str, Any] = {
        "title": title,
        "notes": notes,
        "$type": keeper_type,
        "custom_fields": custom_fields,
    }

    # Only include login fields for login-type records
    if keeper_type == "login":
        record.update({
            "login": login,
            "password": password,
            "login_url": login_url,
        })

    if folders:
        record["folders"] = folders

    return record


def convert_bitwarden_to_keeper_json(src_path: Path, out_path: Path) -> int:
    data = parse_json(src_path)
    id_to_name = build_id_to_name_map(data)

    records: List[Dict[str, Any]] = []
    for item in data.get("items", []) or []:
        if item.get("deletedDate"):
            continue
        records.append(bw_item_to_keeper_record(item, id_to_name))

    out_obj = {
        "shared_folders": [],
        "records": records,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(out_obj, handle, ensure_ascii=False, indent=2)

    return len(records)


def main() -> None:
    src = load_latest_source_json(SOURCE_DIR)
    count = convert_bitwarden_to_keeper_json(src, DEFAULT_OUTPUT)
    print(f"Wrote {count} record(s) to {DEFAULT_OUTPUT.resolve()}")


if __name__ == "__main__":
    main()


