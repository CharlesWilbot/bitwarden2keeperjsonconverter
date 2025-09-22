# Bitwarden to Keeper Converter

Minimal tools to convert Bitwarden JSON exports into Keeper-importable JSON.

## Tools

- `convert_bw_json_to_keeper_json.py`: Converts the latest JSON in `source/` to `target/keeper_import.json`.
- `btok_standalone.py`: Standalone entry that searches for a Bitwarden JSON in the same folder and writes `keeperimportfile.json`.
- `dist/btok.exe`: Portable Windows executable (generated) that performs the same as `btok_standalone.py`.

## Usage

1) Script (dev flow)

- Put Bitwarden export in `source/` (plaintext JSON).
- Run:
  ```bash
  python .\convert_bw_json_to_keeper_json.py
  ```
- Result: `target/keeper_import.json`.

2) Standalone EXE

- Place `btok.exe` and your Bitwarden JSON in the same folder.
- Run `btok.exe`.
- It writes `keeperimportfile.json` in the same folder.

## Mapping

- Title, Notes, `$type` ("login" or "note").
- Login, Password, `login_url` (first URI; `https://` added if missing).
- Custom fields: Bitwarden text -> `$text:<name>:1`, hidden -> `$secret:<name>:1`.
- TOTP: builds `$oneTimeCode::1` as an `otpauth://` URL.
- Folder: uses `folderId` (or first `collectionIds`) as `{ "folder": "..." }`.

## Build (Windows)

- Install PyInstaller:
  ```bash
  python -m pip install pyinstaller
  ```
- Build:
  ```bash
  pyinstaller --noconfirm --clean --onefile --name btok btok_standalone.py
  ```
- Output: `dist/btok.exe`.

## Security

- Exports contain sensitive data. Do not commit any JSON exports.
- `.gitignore` excludes `*.json`, `source/`, `target/`, and build artifacts by default.
- Delete exports after import into Keeper.
