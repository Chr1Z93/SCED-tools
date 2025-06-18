import os
import json

CARD_FOLDER = r"C:\git\SCED-downloads\decomposed\playercards\Baldurs Gate III"
METADATA_FILE = r"C:\git\SCED-tools\scripts\bonded-metadata-data.json"

# Step 1: Load bonded metadata
with open(METADATA_FILE, "r", encoding="utf-8") as f:
    bonded_metadata = json.load(f)

# Step 2: Create a lookup map from card ID to bonded list
bonded_map = {entry["code"]: entry["bound"] for entry in bonded_metadata}

# Step 3: Iterate over .gmnotes files in the card folder
for root, _, files in os.walk(CARD_FOLDER):
    for filename in files:
        if not filename.endswith(".gmnotes"):
            continue

        filepath = os.path.join(root, filename)

    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Skipping invalid JSON file: {filename}")
            continue

    card_id = data.get("id")
    if not card_id:
        print(f"No 'id' field in {filename}, skipping.")
        continue

    if card_id in bonded_map:
        data["bonded"] = bonded_map[card_id]
        print(f"Added bonded data to {filename}")

        # Save updated JSON back to file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        print(f"No bonded data for card {card_id} in {filename}")
