# Checks the embedded metadata for validity

import json
from pathlib import Path

SEARCH_FOLDER = Path(r"C:\git\SCED-downloads\downloadable\other")


def check_gm_notes(json_file_path: Path) -> bool:
    """Returns True if the file is invalid, False otherwise."""
    try:
        with json_file_path.open("r", encoding="utf-8") as f_json:
            json_data = json.load(f_json)

        gm_notes = json_data.get("GMNotes")
        if gm_notes:
            # Attempt to parse the internal JSON string
            json.loads(gm_notes)

        return False  # File is valid

    except (json.JSONDecodeError, KeyError):
        print(f"- Invalid: {json_file_path}")
        return True  # File is invalid
    except Exception as e:
        print(f"- Error processing {json_file_path.name}: {e}")
        return True


def main():
    print(f"Searching for invalid metadata in: {SEARCH_FOLDER}")

    total_scanned = 0
    invalid_count = 0

    # .rglob("*.json") recursively finds all JSON files
    for json_file_path in SEARCH_FOLDER.rglob("*.json"):
        total_scanned += 1
        is_invalid = check_gm_notes(json_file_path)

        if is_invalid:
            invalid_count += 1

    print("-" * 30)
    print(f"Script finished.")
    print(f"Total files scanned: {total_scanned}")
    print(f"Invalid files found: {invalid_count}")


if __name__ == "__main__":
    main()
