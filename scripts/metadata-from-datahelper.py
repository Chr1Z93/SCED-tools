import json
import pandas as pd
import re

# Set the path to the TTS savegame JSON file
SAVE_FILE = r"C:\git\SCED-downloads\downloadable\campaign\darkham_horror.json"
DATAHELPER_FILE = r"C:\git\SCED-tools\scripts\datahelper.json"


# Function to clean up trailing commas in JSON strings
def clean_json(json_str):
    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
    return json_str


# Load metadata from JSON
def load_metadata(file):
    metadata_dict = {}

    card_name = "123"
    metadata = "234"

    metadata_dict[card_name] = metadata

    return metadata_dict


# Step 0: Remove all existing GMNotes
def clear_gmnotes(obj_list):
    for obj in obj_list:
        if "GMNotes" in obj:
            obj["GMNotes"] = ""
        if "ContainedObjects" in obj:
            clear_gmnotes(obj["ContainedObjects"])


# Second pass: Only match by name, skipping objects with non-empty GMNotes
def update_metadata(obj_list, unused_metadata):
    for obj in obj_list:
        # Skip objects with existing GMNotes
        if (obj["Name"] == "Card" or obj["Name"] == "CardCustom") and not obj.get(
            "GMNotes", ""
        ).strip():
            name = obj["Nickname"].strip()

            if name in unused_metadata:
                set_metadata(obj, metadata[name])

                # Remove the (name, description) pair from unused_metadata
                unused_metadata.discard(name)

        # Recursively process contained objects
        if "ContainedObjects" in obj:
            update_metadata(obj["ContainedObjects"], unused_metadata)


def set_metadata(obj, md_value):
    obj["GMNotes"] = md_value  # Store the metadata as GMNotes

    # Initialize Tags as an empty list
    obj["Tags"] = []

    # Parse metadata JSON string
    metadata_dict = json.loads(md_value)

    # Add tags based on metadata conditions
    if metadata_dict.get("type") == "Asset":
        obj["Tags"].append("Asset")
    if metadata_dict.get("type") == "Location":
        obj["Tags"].append("Location")
    if (
        metadata_dict.get("type") == "Location"
        or metadata_dict.get("class") == "Mythos"
    ):
        obj["Tags"].append("ScenarioCard")
    if metadata_dict.get("type") == "Asset" or metadata_dict.get("class") == "Neutral":
        obj["Tags"].append("PlayerCard")


# Load JSON save file
def load_savegame(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


# Save the updated JSON back to file
def save_savegame(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Main execution
if __name__ == "__main__":
    metadata = load_metadata(DATAHELPER_FILE)
    unused_metadata = set(metadata.keys())

    if not metadata:
        print("No valid metadata found. Please fix any JSON errors in the Excel file.")
    else:
        savegame = load_savegame(SAVE_FILE)

        if "ContainedObjects" in savegame:
            # Step 0: Remove metadata
            print("Clearing existing GMNotes ...")
            clear_gmnotes(savegame["ContainedObjects"])

            # Step 1: Apply metadata (if name matches)
            print("Updating metadata ...")
            update_metadata(savegame["ContainedObjects"], metadata, unused_metadata)

        save_savegame(SAVE_FILE, savegame)
        print("\nSavegame update completed.")

        # Output unused metadata entries
        if unused_metadata:
            print("\nThe following metadata entries were not used:")
            for name in unused_metadata:
                print(f"- {name}")
