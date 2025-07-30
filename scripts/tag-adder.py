import os
import json
from pathlib import Path
from collections import OrderedDict

# --- Configuration ---
SEARCH_FOLDER = Path(r"C:\git\SCED-downloads\decomposed")

# Mapping of BackURLs to Tag values
BACK_URL_MAPPING = {
    "https://steamusercontent-a.akamaihd.net/ugc/2342503777940351785/F64D8EFB75A9E15446D24343DA0A6EEF5B3E43DB/": "ScenarioCard",
    "https://steamusercontent-a.akamaihd.net/ugc/2342503777940352139/A2D42E7E5C43D045D72CE5CFC907E4F886C8C690/": "PlayerCard",
    "https://steamusercontent-a.akamaihd.net/ugc/62595146532712476/4F1C745A4BD1E7F5EA6DA68E2D81F59AC2817D22/": "Artifact",
    "https://steamusercontent-a.akamaihd.net/ugc/2453969771999768294/54768C2E562D30E34B79EB7A94FCDC792E49FC28/": "EnemyDeck",
    "https://steamusercontent-a.akamaihd.net/ugc/1814412497119682452/BD224FCE1980DBA38E5A687FABFD146AA1A30D0E/": "UpgradeSheet",
}


# --- Helper Functions ---
def update_card_tags(json_file_path: Path, managed_tags: set):
    with open(json_file_path, "r", encoding="utf-8") as f_json:
        json_data = json.load(f_json)

    updated = False

    # Skip decks
    if json_data.get("Name") == "Deck":
        return

    # Initialize current_tags safely
    current_tags = []
    if "Tags" in json_data and isinstance(json_data["Tags"], list):
        current_tags = list(json_data["Tags"])  # Make a mutable copy

    # Use a set to build new tags, automatically handling uniqueness
    new_tags_set = set()

    # Preserve existing tags that are NOT managed by this script
    for existing_tag in current_tags:
        if existing_tag not in managed_tags:
            new_tags_set.add(existing_tag)

    # Check BackURL for tag
    if "CustomDeck" in json_data and isinstance(json_data["CustomDeck"], dict):
        for _, deck_data in json_data["CustomDeck"].items():
            if deck_data["BackURL"] in BACK_URL_MAPPING:
                new_tags_set.add(BACK_URL_MAPPING[deck_data["BackURL"]])
            else:
                return

    # Check for metadata
    if json_data.get("GMNotes_path") or json_data.get("GMNotes"):
        # Check for 'type' field
        card_type = ...
        if card_type == "Asset" or card_type == "Location":
            new_tags_set.add(card_type)
    else:
        # Keep existing Asset/Location tag
        for existing_tag in current_tags:
            if existing_tag == "Asset" or existing_tag == "Location":
                new_tags_set.add(existing_tag)

    # Convert the set of new tags to a sorted list for consistent output and comparison
    final_tags = sorted(list(new_tags_set))

    # Check if the tags have actually changed compared to the original sorted tags
    if sorted(current_tags) != final_tags:
        json_data["Tags"] = final_tags
        updated = True

    if updated:
        sorted_json_data = OrderedDict(sorted(json_data.items()))

        with open(json_file_path, "w", encoding="utf-8") as f_json:
            json.dump(sorted_json_data, f_json, indent=2)
            f_json.write("\n")  # Add an empty line at the end of the file
        print(f"Updated Tags in {json_file_path}")


# --- Main Execution ---
def main():
    print(f"Starting script to update tags in: {SEARCH_FOLDER}")

    # Create a set of all possible tag values that this script manages.
    # This is crucial for correctly removing outdated tags if their conditions change.
    all_managed_tags = set(BACK_URL_MAPPING.values())
    all_managed_tags.add("Asset")
    all_managed_tags.add("Location")

    for root, _, files in os.walk(SEARCH_FOLDER):
        for file_name in files:
            if file_name.endswith(".json"):
                json_file_path = Path(root) / file_name
                update_card_tags(json_file_path, all_managed_tags)

    print(f"\nScript finished.")


if __name__ == "__main__":
    main()
