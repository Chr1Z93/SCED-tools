import os
import json
from pathlib import Path
from collections import OrderedDict

# --- Configuration ---
SEARCH_FOLDER = Path(r"C:\git\SCED-downloads\decomposed")

# Define your mapping of BackURLs to Tag values
BACK_URL_MAPPING = {
    "https://steamusercontent-a.akamaihd.net/ugc/2342503777940351785/F64D8EFB75A9E15446D24343DA0A6EEF5B3E43DB/": "ScenarioCard",
    "https://steamusercontent-a.akamaihd.net/ugc/2342503777940352139/A2D42E7E5C43D045D72CE5CFC907E4F886C8C690/": "PlayerCard",
    "https://steamusercontent-a.akamaihd.net/ugc/62595225072308126/139A17D2C1EDA5DA8047BC22855BD58F15FF03C8/": "Artifact",
    "https://steamusercontent-a.akamaihd.net/ugc/2453969771999768294/54768C2E562D30E34B79EB7A94FCDC792E49FC28/": "EnemyDeck",
    "https://steamusercontent-a.akamaihd.net/ugc/1814412497119682452/BD224FCE1980DBA38E5A687FABFD146AA1A30D0E/": "UpgradeSheet",
}


# --- Helper Functions ---
def update_card_tags(json_file_path: Path, back_url_mapping: dict):
    print(f"Processing {json_file_path}...")

    with open(json_file_path, "r", encoding="utf-8") as f_json:
        json_data = json.load(f_json)

    updated = False

    if "CustomDeck" in json_data and isinstance(json_data["CustomDeck"], dict):
        for _, deck_data in json_data["CustomDeck"].items():
            if deck_data["BackURL"] not in back_url_mapping:
                continue

            tag_to_add = back_url_mapping[deck_data["BackURL"]]

            if "Tags" not in json_data:
                json_data["Tags"] = []

            if tag_to_add not in json_data["Tags"]:
                json_data["Tags"].append(tag_to_add)
                updated = True
                print(f"  - Added tag '{tag_to_add}' based on BackURL match.")

    if updated:
        sorted_json_data = OrderedDict(sorted(json_data.items()))

        with open(json_file_path, "w", encoding="utf-8") as f_json:
            json.dump(sorted_json_data, f_json, indent=2)
            f_json.write("\n")  # Add an empty line at the end of the file
        print(f"Updated Tags in {json_file_path}")


# --- Main Execution ---
def main():
    print(f"Starting script to update tags based on BackURL in: {SEARCH_FOLDER}")

    for root, _, files in os.walk(SEARCH_FOLDER):
        for file_name in files:
            if file_name.endswith(".json"):
                json_file_path = Path(root) / file_name
                update_card_tags(json_file_path, BACK_URL_MAPPING)

    print(f"\nScript finished.")


if __name__ == "__main__":
    main()
