import json
import os
from pathlib import Path
import requests
from tool_gui import ToolGUI

# Globals / Derived data
DATA_API_URL = "https://api.arkham.build/v1/cache/cards/en"

# Folders that should never be processed
EXCLUDED_DIRS = {".git", ".github", ".vscode"}

# Setup for the GUI
OPTIONS = {
    "input_folder": {
        "type": "folder",
        "label": "Input folder",
        "default": r"C:\git\SCED-downloads\decomposed\language-pack\Spanish - Campaigns",
    },
    "types": {
        "type": "multiselect",
        "label": "Card Types",
        "values": ["act", "agenda", "location", "scenario", "enemy", "treachery"],
        "default": ["act", "agenda", "scenario"],
    },
    "encounters": {
        "type": "multiselect",
        "label": "Encounter Sets",
        "values": [
            "the_unspeakable_oath",
            "black_stars_rise",
            "a_phantom_of_truth",
            "the_pallid_mask",
        ],
    },
}


# This swaps the FaceURL and BackURL of specific cards
def update_json_files_in_folder(log, input_folder, types, encounters):
    if not input_folder.exists():
        log(f"Error: The directory {input_folder} was not found.")
        return

    api_data = load_api_data()
    missing_api_ids = set()
    flipped_count = 0

    for root, dirs, files in os.walk(input_folder):
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

                # Skip cards that don't have type / are single-sided
                item = api_data[adb_id]
                if "type_code" not in item or not item.get("double_sided"):
                    continue

                # Skip unwanted cards
                type_code = item["type_code"].lower()
                if type_code not in types:
                    continue

                encounter_code = item["encounter_code"].lower()
                if encounter_code not in encounters:
                    continue

                # Swap URLs
                flip_card(data)
                flipped_count += 1

                with file_path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")

                log(f"Flipped file: {file} ({adb_id})")

            except json.JSONDecodeError:
                log(f"Invalid JSON: {file_path}")
                continue

    for id in sorted(missing_api_ids):
        log(f"Missing API:  {id}")

    log(f"Summary: Flipped {flipped_count} cards.")


def load_api_data():
    api_data = {}
    try:
        response = requests.get(DATA_API_URL, timeout=15)
        response.raise_for_status()

        for item in response.json()["data"]["all_card"]:
            api_data[item["code"]] = item

    except requests.RequestException as e:
        print(f"Couldn't get card data: {e}")
    except json.JSONDecodeError:
        print(f"Couldn't parse API response")

    return api_data


def flip_card(data):
    custom_deck = data["CustomDeck"]
    deck_id = next(iter(custom_deck))
    card_details = custom_deck[deck_id]
    card_details["FaceURL"], card_details["BackURL"] = (
        card_details["BackURL"],
        card_details["FaceURL"],
    )


def run_tool(config, log):
    folder = Path(config["input_folder"])
    types = set(config["types"])
    encounters = set(config["encounters"])
    update_json_files_in_folder(log, folder, types, encounters)


if __name__ == "__main__":
    ToolGUI("Flip Arkham Cards", OPTIONS, run_tool).show()
