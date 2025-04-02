import json
import pandas as pd

# Set the path to the TTS savegame JSON file
SAVEGAME_PATH = (
    r"C:\git\SCED-downloads\downloadable\campaign\call_of_the_plaguebearer.json"
)
METADATA_FILE = r"C:\git\SCED-tools\scripts\metadata.xlsx"


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
        metadata = row["Metadata"].strip()

        # Validate JSON format
        try:
            json.loads(metadata)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON at row {index + 2} (Excel row {index + 2}): {e}")
            continue

        if card_description:  # Only use description if it's not empty
            metadata_dict[(card_name, card_description)] = metadata

        # Always store with empty description as fallback
        metadata_dict[(card_name, "")] = metadata

    return metadata_dict


# Recursively update GMNotes in the save file
def update_gmnotes(obj_list, metadata, unused_metadata):
    for obj in obj_list:
        if "Nickname" in obj:
            name = obj["Nickname"].strip()
            description = obj.get("Description", "").strip()

            # Match using Name and Description if necessary
            value = metadata.get((name, description)) or metadata.get((name, ""))
            if value:
                obj["GMNotes"] = value
                # Log only if description is non-empty
                if description:
                    print(f"Updated GMNotes for: {name} ({description})")
                else:
                    print(f"Updated GMNotes for: {name}")
                unused_metadata.discard((name, description))
                unused_metadata.discard((name, ""))

        # Recursively update contained objects
        if "ContainedObjects" in obj:
            update_gmnotes(obj["ContainedObjects"], metadata, unused_metadata)


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
        print("No valid metadata found. Please fix any JSON errors in metadata.xlsx.")
    else:
        savegame = load_savegame(SAVEGAME_PATH)

        if "ContainedObjects" in savegame:
            update_gmnotes(savegame["ContainedObjects"], metadata, unused_metadata)

        save_savegame(SAVEGAME_PATH, savegame)
        print("Savegame updated successfully!")

        # Output unused metadata entries
        if unused_metadata:
            print("The following metadata entries were not used:")
            for name, description in unused_metadata:
                # Log only if description is non-empty
                if description:
                    print(f"- {name} ({description})")
                else:
                    print(f"- {name}")
