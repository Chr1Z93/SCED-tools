# Checks the embedded metadata for validity

import os
import json
from pathlib import Path

SEARCH_FOLDER = Path(r"C:\git\SCED-downloads\decomposed")


def check_gm_notes(json_file_path: Path):
    with open(json_file_path, "r", encoding="utf-8") as f_json:
        json_data = json.load(f_json)

    gm_notes = json_data.get("GMNotes")
    if gm_notes and gm_notes != "":
        try:
            gmnotes_data = json.loads(json_data["GMNotes"])
        except json.JSONDecodeError:
            print(f"- Invalid: {json_file_path}")


def main():
    print(f"Searching for invalid metadata...")

    for root, _, files in os.walk(SEARCH_FOLDER):
        for file_name in files:
            if file_name.endswith(".json"):
                json_file_path = Path(root) / file_name
                check_gm_notes(json_file_path)

    print(f"\nScript finished.")


if __name__ == "__main__":
    main()
