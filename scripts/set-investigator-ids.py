# Sets IDs for investigators from the Zoop GUIDs

import os
import json

CARD_FOLDER = r"C:\git\SCED-downloads\decomposed\playercards\Baldurs Gate III"

for root, _, files in os.walk(CARD_FOLDER):
    for filename in files:
        if not filename.endswith(".gmnotes"):
            continue

        filepath = os.path.join(root, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON: {filepath}")
                continue

        # Only proceed if type is "Investigator"
        if data.get("type") != "Investigator":
            continue

        if "ID" not in data:
            if "TtsZoopGuid" in data:
                data["ID"] = data["TtsZoopGuid"]
                print(f"Added ID to {filepath}")

                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            else:
                print(f"No TtsZoopGuid found in {filepath}; cannot add ID")
