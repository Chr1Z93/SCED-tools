import json
import pandas as pd
import re
import sys

# Set the path to the TTS savegame JSON file
SAVE_FILE = r"C:\Users\pulsc\Documents\My Games\Tabletop Simulator\Saves\Saved Objects\TDC_WIP.json"
METADATA_FILE = r"C:\git\SCED-tools\scripts\metadata-tdc.xlsx"


# Function to clean up trailing commas in JSON strings
def clean_json(json_str):
    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
    return json_str


# Load metadata from Excel and validate JSON
def load_metadata(file):
    df = pd.read_excel(file, dtype=str)
    metadata_dict = {}

    for index, row in df.iterrows():
        card_name = row["Card Name"].strip()
        card_type = row["Type"].strip()
        card_description = (
            str(row["Card Description"]).strip()
            if pd.notna(row["Card Description"])
            else ""
        )
        id = row["ID"].strip()
        metadata = clean_json(row["Metadata"].strip())

        try:
            json.loads(metadata)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON at row {index + 2}: {e}")
            continue

        metadata_dict[id] = {
            "Nickname": card_name,
            "Description": card_description,
            "GMNotes": metadata,
            "Type": card_type,
        }

    return metadata_dict


# Recursively update GMNotes in the save file
def update_metadata(obj_list, metadata, unused_metadata):
    for obj in obj_list:
        if obj["Name"] == "Card" or obj["Name"] == "CardCustom":
            # Try exact match (assuming the name is the ID)
            name = obj["Nickname"].strip()
            md_value = metadata.get(name)

            if md_value:
                set_metadata(obj, md_value)
                print(f"Updated metadata for: {name}")

                # Remove the data from the unused metadata list
                unused_metadata.discard(name)

        # Recursively update contained objects
        if "ContainedObjects" in obj:
            update_metadata(obj["ContainedObjects"], metadata, unused_metadata)


def set_metadata(obj, md_value):
    # Set nickname and description
    obj["Nickname"] = md_value["Nickname"]
    obj["Description"] = md_value["Description"]

    # Initialize Tags as an empty list
    obj["Tags"] = []

    # Parse metadata JSON string
    metadata_dict = json.loads(md_value["GMNotes"])

    # Force correct cycle data
    metadata_dict["cycle"] = "The Drowned City"

    # Force correct type data
    metadata_dict["type"] = md_value["Type"]

    obj["GMNotes"] = json.dumps(metadata_dict)

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
    metadata = load_metadata(METADATA_FILE)
    unused_metadata = set(metadata.keys())

    if not metadata:
        print("No valid metadata found. Please fix any JSON errors in the Excel file.")
    else:
        savegame = load_savegame(SAVE_FILE)

        # Change this to "ContainedObjects" for loadable objects
        if "ObjectStates" in savegame:
            update_metadata(savegame["ObjectStates"], metadata, unused_metadata)

        save_savegame(SAVE_FILE, savegame)
        print("\nSavegame updated successfully!")

        # Output unused metadata entries
        if unused_metadata:
            print("\nThe following metadata entries were not used:")
            for id in unused_metadata:
                entry = metadata[id]
                name = entry["Nickname"]
                description = entry["Description"]
                print(
                    f"- {id} {name}"
                    if not description
                    else f"- {id} {name} ({description})"
                )
