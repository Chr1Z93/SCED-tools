# Removes duplicate cards

import os
import json
from pathlib import Path

# --- Configuration ---
SEARCH_FOLDER = Path(
    r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Korean - Campaigns"
)

REMOVE_BY_GM_NOTES = True

# --- Main Logic ---
card_id_map = {}
gm_notes_map = {}


def main():
    print(f"Scanning folder: {SEARCH_FOLDER}")

    for root, dirs, files in os.walk(SEARCH_FOLDER):
        if ".git" in dirs:
            dirs.remove(".git")

        if ".vscode" in dirs:
            dirs.remove(".vscode")

        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            file_path = Path(root) / file_name

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Warning: Could not decode JSON file {file_path}. Error: {e}")
                continue

            if REMOVE_BY_GM_NOTES:
                gm_notes = json_data.get("GMNotes")
                if not gm_notes:
                    continue

                if gm_notes in gm_notes_map:
                    os.remove(file_path)
                else:
                    gm_notes_map[gm_notes] = True
            else:
                card_id = json_data.get("CardID")
                if not card_id:
                    continue

                if card_id in card_id_map:
                    os.remove(file_path)
                else:
                    card_id_map[card_id] = True

    print("\nScript finished.")


if __name__ == "__main__":
    main()
