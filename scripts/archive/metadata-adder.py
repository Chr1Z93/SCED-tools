import json
import pandas as pd
import re

# Set the path to the TTS savegame JSON file
SAVE_FILE = r"C:\git\SCED-downloads\downloadable\campaign\call_of_the_plaguebearer.json"
METADATA_FILE = r"C:\git\SCED-tools\scripts\metadata-adder-CoP.xlsx"


# Function to clean up trailing commas in JSON strings
def clean_json(json_str):
    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
    return json_str


# Load metadata from Excel and validate JSON
def load_metadata(file):
    df = pd.read_excel(file, dtype=str)
    metadata_dict = {}

    for index, row in df.iterrows():
        card_name = row["Card Name"].strip()
        # Handle NaN values and convert them to empty string
        card_description = (
            str(row["Card Description"]).strip()
            if pd.notna(row.get("Card Description"))
            else ""
        )
        metadata = clean_json(row["Metadata"].strip())

        try:
            json.loads(metadata)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON at row {index + 2}: {e}")  # type: ignore
            continue

        metadata_dict[(card_name, card_description)] = metadata

    return metadata_dict


# Step 0: Remove all existing GMNotes
def clear_gmnotes(obj_list):
    for obj in obj_list:
        if "GMNotes" in obj:
            obj["GMNotes"] = ""
        if "ContainedObjects" in obj:
            clear_gmnotes(obj["ContainedObjects"])


# Recursively update GMNotes in the save file
def update_gmnotes(obj_list, metadata, unused_metadata):
    for obj in obj_list:
        if obj["Name"] == "Card" or obj["Name"] == "CardCustom":
            name = obj["Nickname"].strip()
            description = obj["Description"].strip()

            # Try exact match (Name + Description)
            md_value = metadata.get((name, description))

            # If no match, check if name follows "name (description)" format
            match = None  # Ensure match is always defined
            if not md_value:
                # Extract name and description
                match = re.match(r"^(.*) \((.*)\)$", name)
                if match:
                    ex_name, ex_description = match.groups()
                    md_value = metadata.get((ex_name.strip(), ex_description.strip()))

            if md_value:
                set_metadata(obj, md_value)
                print(f"Updated GMNotes in 1st pass for: {name}")

                # Remove the data from the unused metadata list
                unused_metadata.discard((name, description))
                unused_metadata.discard((name, ""))
                if match:
                    unused_metadata.discard((ex_name.strip(), ex_description.strip()))
                    unused_metadata.discard((ex_name.strip(), ""))

        # Recursively update contained objects
        if "ContainedObjects" in obj:
            update_gmnotes(obj["ContainedObjects"], metadata, unused_metadata)


# Second pass: Only match by name (ignoring descriptions), skipping objects with non-empty GMNotes
def second_pass_update(obj_list, unused_metadata):
    for obj in obj_list:
        # Skip objects with existing GMNotes
        if (obj["Name"] == "Card" or obj["Name"] == "CardCustom") and not obj.get(
            "GMNotes", ""
        ).strip():
            name = obj["Nickname"].strip()

            # Get all metadata keys matching the name (regardless of description)
            matching_keys = {(n, d) for (n, d) in unused_metadata if n == name}

            if matching_keys:
                # Find the metadata entry to apply (use first match or any available)
                md_value = None
                description_used = None
                for key in matching_keys:
                    if key in metadata:
                        md_value = metadata[key]
                        description_used = key[1]  # The description part of the key
                        break

                if md_value:
                    set_metadata(obj, md_value)
                    print(f"Updated GMNotes in 2nd pass for: {name}")

                    # Remove the (name, description) pair from unused_metadata
                    unused_metadata.discard((name, description_used))

        # Recursively process contained objects
        if "ContainedObjects" in obj:
            second_pass_update(obj["ContainedObjects"], unused_metadata)

import json


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
    metadata = load_metadata(METADATA_FILE)
    unused_metadata = set(metadata.keys())

    if not metadata:
        print("No valid metadata found. Please fix any JSON errors in the Excel file.")
    else:
        savegame = load_savegame(SAVE_FILE)

        if "ContainedObjects" in savegame:
            # Step 0: Remove metadata
            print("Clearing existing GMNotes...")
            clear_gmnotes(savegame["ContainedObjects"])

            # Step 1: Apply metadata (full match first)
            update_gmnotes(savegame["ContainedObjects"], metadata, unused_metadata)

            # Step 2: Second pass (name-only, skipping non-empty GMNotes)
            if unused_metadata:
                print("\nSecond pass (name-only, skipping non-empty GMNotes)...")
                second_pass_update(savegame["ContainedObjects"], unused_metadata)

        save_savegame(SAVE_FILE, savegame)
        print("\nSavegame updated successfully!")

        # Output unused metadata entries
        if unused_metadata:
            print("\nThe following metadata entries were not used:")
            for name, description in unused_metadata:
                print(f"- {name}" if description == "" else f"- {name} ({description})")
