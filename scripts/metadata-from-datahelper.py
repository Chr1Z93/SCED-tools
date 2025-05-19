import json
import re

# Set the path to the TTS savegame JSON file
SAVE_FILE = r"C:\Users\pulsc\Documents\My Games\Tabletop Simulator\Saves\Saved Objects\Darkham Horror.json"
DATAHELPER_FILE = r"C:\git\SCED-tools\scripts\datahelper.json"
CYCLE_NAME = "Darkham Horror"

# Function to clean up trailing commas in JSON strings
def clean_json(json_str):
    # Remove trailing commas before closing braces/brackets
    json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
    return json_str


# Load metadata from JSON
def load_metadata():
    datahelper = load_JSON(DATAHELPER_FILE)

    metadata_dict = {}

    for card_name, info in datahelper.items():
        # handle location data
        if "clueSide" in info:
            token_entry = {"type": "Clue", "token": "clue"}

            if info["type"] == "perPlayer":
                token_entry["countPerInvestigator"] = info["value"]
            elif info["type"] == "fixed":
                token_entry["count"] = info["value"]
            else:
                raise ValueError(
                    f"Unknown type '{info['type']}' for card '{card_name}'"
                )

            location_side = (
                "locationFront" if info["clueSide"] == "front" else "locationBack"
            )

            metadata = {
                "id": "",
                "type": "Location",
                location_side: {"icons": "", "connections": "", "uses": [token_entry]},
                "cycle": CYCLE_NAME,
            }

            metadata_dict[card_name] = metadata
        else:
            metadata = {
                "id": "",
                "type": "Asset",
                "uses": {
                    "type": info["tokenType"].capitalize(),
                    "token": info["tokenType"],
                    "count": info["tokenCount"],
                },
                "cycle": CYCLE_NAME,
            }
            metadata_dict[card_name] = metadata

    return metadata_dict


# Remove all existing GMNotes
def clear_gmnotes(obj_list):
    for obj in obj_list:
        if "GMNotes" in obj:
            obj["GMNotes"] = ""
        if "ContainedObjects" in obj:
            clear_gmnotes(obj["ContainedObjects"])


# Match by name
def update_metadata(obj_list, metadata, unused_metadata):
    for obj in obj_list:
        # Skip non-card objects
        if obj["Name"] == "Card" or obj["Name"] == "CardCustom":
            name = obj["Nickname"]

            if name in unused_metadata:
                set_metadata(obj, metadata[name])

                # Remove the name from unused_metadata
                unused_metadata.discard(name)

        # Recursively process contained objects
        if "ContainedObjects" in obj:
            update_metadata(obj["ContainedObjects"], metadata, unused_metadata)


def set_metadata(obj, md_value):
    obj["GMNotes"] = clean_json(json.dumps(md_value, separators=(",", ":")))

    # Initialize Tags as an empty list
    obj["Tags"] = []

    # Add tags based on metadata conditions
    if md_value.get("type") == "Asset":
        obj["Tags"].append("Asset")
        obj["Tags"].append("PlayerCard")
    if md_value.get("type") == "Location":
        obj["Tags"].append("Location")
        obj["Tags"].append("ScenarioCard")


# Load JSON save file
def load_JSON(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


# Save the updated JSON back to file
def save_savegame(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# Main execution
if __name__ == "__main__":
    metadata = load_metadata()
    unused_metadata = set(metadata.keys())
    savegame = load_JSON(SAVE_FILE)

    outer_layer = None
    index_in_objectstates = 0  # Default to first item if relevant

    # Detect and extract nested ObjectStates structure
    if "ObjectStates" in savegame:
        outer_layer = savegame.copy()
        object_states = outer_layer["ObjectStates"]

        if isinstance(object_states, list) and object_states:
            savegame = object_states[index_in_objectstates]
        else:
            raise ValueError("ObjectStates is empty or not a list.")

    if "ContainedObjects" in savegame:
        # Remove metadata
        print("Clearing existing GMNotes ...")
        clear_gmnotes(savegame["ContainedObjects"])

        # Apply metadata (if name matches)
        print("Updating metadata ...")
        update_metadata(savegame["ContainedObjects"], metadata, unused_metadata)

        # Restore the outer layer if it was present
        if outer_layer is not None:
            outer_layer["ObjectStates"][index_in_objectstates] = savegame
            savegame_to_save = outer_layer
        else:
            savegame_to_save = savegame

        # Save the game
        print("Savegame update completed.")
        save_savegame(SAVE_FILE, savegame_to_save)

        # Output unused metadata entries
        if unused_metadata:
            print("The following metadata entries were not used:")
            for name in unused_metadata:
                print(f"- {name}")
