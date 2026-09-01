import json
import sys
from pathlib import Path
import bson

# Default local path for Tabletop Simulator's CloudInfo.bson
DEFAULT_BSON_PATH = r"D:\Steam\userdata\86524646\286160\remote\CloudInfo.bson"


def read_local_cloud_info_bson(file_path):
    """Read and decode CloudInfo.bson directly from the local filesystem."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Could not find '{path.resolve()}'.")

    bson_bytes = path.read_bytes()

    if not bson_bytes:
        raise ValueError(f"The file '{path}' is empty (0 bytes).")

    try:
        return bson.decode(bson_bytes)
    except Exception as e:
        raise RuntimeError(f"Failed to parse local BSON file.\nDetails: {e}")


def normalize_cloud_path(path_str):
    """Clean and normalize cloud directory paths."""
    if not path_str:
        return ""
    path_str = str(path_str).strip().replace("\\", "/")
    parts = [p for p in path_str.split("/") if p]
    return "/".join(parts)


def process_cloud_rows(raw_data):
    """Extract standard row fields."""
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
    print(f"Successfully exported {len(data)} items to {output_file}")


def main():
    # If passed as an argument, use custom path; otherwise use local DEFAULT_BSON_PATH
    bson_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BSON_PATH

    print(f"Reading local file: {bson_file}...")
    raw_bson = read_local_cloud_info_bson(bson_file)

    # Format and standardize rows
    rows = process_cloud_rows(raw_bson)
    print(f"Found {len(rows)} indexed files in BSON payload.")

    # Export JSON
    export_to_json(rows, "tts_cloud_info.json")


if __name__ == "__main__":
    main()
