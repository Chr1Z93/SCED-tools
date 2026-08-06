# This swaps the FaceURL and BackURL of specified card types

import json
import os
from pathlib import Path
import requests

# CONFIGURATION
# ----------------------------------------------
# Folder to process
INPUT_FOLDER = Path(r"C:\git\SCED-downloads\decomposed\language-pack\Spanish - Campaigns\Spanish-Campaigns.SpanishC")

# Card types to flip (lowercase)
# Example: treachery, scenario, location, enemy, act, agenda
TYPE_FILTER = {"act", "agenda"}

# Encounter codes to flip (lowercase)
ENCOUNTER_CODE_FILTER = {"the_unspeakable_oath", "black_stars_rise", "a_phantom_of_truth", "the_pallid_mask"}

# Globals / Derived data
DATA_API_URL = "https://api.arkham.build/v1/cache/cards/en"

# Folders that should never be processed
EXCLUDED_DIRS = {".git", ".github", ".vscode"}


def load_api_data():
    api_data = {}
    try:
        response = requests.get(DATA_API_URL, timeout=15)
        response.raise_for_status()

        # Create a lookup map
        for item in response.json()["data"]["all_card"]:
            if "type_code" not in item or not item.get("double_sided"):
                continue

            api_data[item["code"]] = item

    except requests.RequestException as e:
        print(f"Couldn't get card data: {e}")
    except json.JSONDecodeError:
        print(f"Couldn't parse API response")

    return api_data


def update_json_files_in_folder():
    if not INPUT_FOLDER.exists():
        print(f"Error: The directory {INPUT_FOLDER} was not found.")
        return

    api_data = load_api_data()

    missing_api_ids = set()
    flipped_count = 0

    for root, dirs, files in os.walk(INPUT_FOLDER):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        root = Path(root)

        for file in files:
            if not file.endswith(".json"):
                continue

            file_path = root / file

            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            # Only process cards
            if data.get("Name") not in {"Card", "CardCustom"}:
                continue

            # Skip cards without GMNotes
            if "GMNotes" not in data:
                continue

            try:
                md = json.loads(data["GMNotes"])
                adb_id = md.get("id")
                if not adb_id:
                    continue

                # Skip cards without API data
                if adb_id not in api_data:
                    missing_api_ids.add(adb_id)
                    continue

                # Skip unwanted cards
                type_code = api_data[adb_id]["type_code"].lower()
                if type_code not in TYPE_FILTER:
                    continue

                encounter_code = api_data[adb_id]["encounter_code"].lower()
                if encounter_code not in ENCOUNTER_CODE_FILTER:
                    continue

                # Swap URLs
                flip_card(data)
                flipped_count += 1

                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")

                print(f"Flipped file: {file_path} ({adb_id})")

            except json.JSONDecodeError:
                print(f"Invalid JSON: {file_path}")
                continue

    for id in sorted(missing_api_ids):
        print(f"Skipped {id} (missing data)")

    print(f"Finished. Flipped {flipped_count} cards.")


def flip_card(data):
    custom_deck = data["CustomDeck"]
    deck_id = next(iter(custom_deck))
    card_details = custom_deck[deck_id]
    card_details["FaceURL"], card_details["BackURL"] = (
        card_details["BackURL"],
        card_details["FaceURL"],
    )


if __name__ == "__main__":
    update_json_files_in_folder()
