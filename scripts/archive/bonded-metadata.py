# Adds the bonded metadata for decomposed card data from an arkham.build export

import os
import json

CARD_FOLDER = r"C:\git\SCED-downloads\decomposed\playercards\Baldurs Gate III"
METADATA_FILE = r"C:\git\SCED-tools\scripts\bonded-metadata-data.json"

# Load bonded metadata
with open(METADATA_FILE, "r", encoding="utf-8") as f:
    bonded_metadata = json.load(f)

# Create lookup map from card ID to bonded list
bonded_map = {entry["code"]: entry["bound"] for entry in bonded_metadata}

# Recursively walk through all subfolders
for root, _, files in os.walk(CARD_FOLDER):
    for filename in files:
        if not filename.endswith(".gmnotes"):
            continue

        filepath = os.path.join(root, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON file: {filepath}")
                continue

        card_id = data.get("id") or data.get("TtsZoopGuid")
        if not card_id:
            print(f"No 'id' field in {filepath}, skipping.")
            continue

        if card_id in bonded_map:
            data["bonded"] = bonded_map[card_id]
            print(f"Added bonded data to {filepath}")

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
