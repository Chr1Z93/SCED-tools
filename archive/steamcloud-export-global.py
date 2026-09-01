import csv
import json
import sys
from pathlib import Path
import bson

# Tabletop Simulator App ID
TTS_APP_ID = 286160


def init_steam():
    """Initialize Steamworks API for Tabletop Simulator."""
    # Write steam_appid.txt temporarily so Steamworks attaches to TTS
    appid_file = Path("steam_appid.txt")
    wrote_appid = not appid_file.exists()

    if wrote_appid:
        appid_file.write_text(str(TTS_APP_ID))

    try:
        from steamworks import STEAMWORKS

        steam = STEAMWORKS()
        steam.initialize()
        return steam
    except Exception as e:
        print(
            f"Error: Could not initialize Steamworks API. Is Steam running?\nDetails: {e}"
        )
        sys.exit(1)
    finally:
        if wrote_appid and appid_file.exists():
            try:
                appid_file.unlink()
            except OSError:
                pass


def read_cloud_info_bson(steam):
    """Read CloudInfo.bson directly from Steam RemoteStorage."""
    if not steam.RemoteStorage.FileExists("CloudInfo.bson"):
        raise FileNotFoundError(
            "CloudInfo.bson was not found in Tabletop Simulator's Steam Cloud."
        )

    # Get file size and read byte content
    file_size = steam.RemoteStorage.GetFileSize("CloudInfo.bson")
    if file_size <= 0:
        raise ValueError(f"CloudInfo.bson appears to be empty (size: {file_size}).")

    # Read binary contents
    bson_bytes = steam.RemoteStorage.FileRead("CloudInfo.bson", file_size)

    # Parse BSON data
    try:
        return bson.decode(bson_bytes)
    except Exception as e:
        # Dump for debugging if parsing fails
        dump_path = Path("CloudInfo.bson.dump")
        dump_path.write_bytes(bson_bytes)
        raise RuntimeError(
            f"Failed to parse BSON. Raw binary dumped to {dump_path}\nDetails: {e}"
        )


def normalize_cloud_path(path_str):
    """Clean and normalize cloud directory paths."""
    if not path_str:
        return ""
    path_str = str(path_str).strip().replace("\\", "/")
    parts = [p for p in path_str.split("/") if p]
    return "/".join(parts)


def process_cloud_rows(raw_data):
    """Extract standard row fields matching the JavaScript implementation."""
    rows = []
    if not isinstance(raw_data, dict):
        raise ValueError("CloudInfo.bson root must be a key-value structure.")

    for key, value in raw_data.items():
        if not isinstance(value, dict):
            continue

        # Extract fields with fallback casing
        name = value.get("Name") or value.get("name") or ""
        url = value.get("URL") or value.get("Url") or value.get("url") or ""
        folder = value.get("Folder") or value.get("folder") or ""
        size = value.get("Size") or value.get("size") or 0

        rows.append(
            {
                "key": str(key),
                "Name": str(name),
                "URL": str(url),
                "Folder": normalize_cloud_path(folder),
                "Size": int(size) if str(size).isdigit() else 0,
            }
        )

    return rows


def export_to_json(data, output_file):
    """Save structured records to JSON."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" Successfully exported {len(data)} items to {output_file}")


def export_to_csv(data, output_file):
    """Save structured records to CSV."""
    fieldnames = ["key", "Name", "URL", "Folder", "Size"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f" Successfully exported {len(data)} items to {output_file}")


def main():
    print("Connecting to Steam API...")
    steam = init_steam()

    # Retrieve user profile info
    persona_name = steam.Users.GetPersonaName()
    print(f"Logged in as: {persona_name}")

    print("Fetching CloudInfo.bson from Steam Cloud...")
    raw_bson = read_cloud_info_bson(steam)

    # Format and standardize rows
    rows = process_cloud_rows(raw_bson)
    print(f"Found {len(rows)} indexed files in CloudInfo.bson.")

    # Export both JSON and CSV
    export_to_json(rows, "tts_cloud_info.json")
    export_to_csv(rows, "tts_cloud_info.csv")


if __name__ == "__main__":
    main()
