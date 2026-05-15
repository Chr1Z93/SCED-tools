from pathlib import Path
import json

PROJECT_PATH = Path(
    r"C:\git\SCED-downloads\decomposed\campaign\Rise, Rapture, Rise\RiseRaptureRise.412e0a"
)
SAVED_OBJECT_PATH = Path(
    r"C:\Users\pulsc\Documents\My Games\Tabletop Simulator\Saves\Saved Objects\Rise Rapture Rise.json"
)


def get_id(metadata):
    if not isinstance(metadata, dict):
        return None
    return metadata.get("id") or metadata.get("TtsZoopGuid")


def parse_gmnotes(raw_notes):
    if not isinstance(raw_notes, str):
        return None

    try:
        return get_id(json.loads(raw_notes.strip()))
    except json.JSONDecodeError:
        return None


def get_metadata(file_path, file_data):
    """
    Checks the .gmnotes file first. If not found, uses the
    already-loaded file_data dictionary.
    """
    gmnotes_file = file_path.with_suffix(".gmnotes")

    # Try separate file first
    if gmnotes_file.exists():
        try:
            with open(gmnotes_file, "r", encoding="utf-8") as f:
                return get_id(json.load(f))
        except json.JSONDecodeError:
            pass

    # Fallback to the already-parsed in-memory internal data
    return parse_gmnotes(file_data.get("GMNotes"))


def build_update_map(obj, update_map):
    """Recursively crawls the saved object to map IDs to URLs."""
    if obj.get("Name") in ["Card", "CardCustom"]:
        # Check if this specific object has the metadata we need
        obj_id = parse_gmnotes(obj.get("GMNotes"))

        if obj_id:
            # TTS stores URLs in the CustomDeck dictionary
            deck_values = list(obj["CustomDeck"].values())
            if deck_values:
                data = deck_values[0]
                sorted_data = {k: data[k] for k in sorted(data.keys())}
                update_map[obj_id] = sorted_data

    # Recurse into containers (Bags, Decks, etc.)
    for child in obj.get("ContainedObjects", []):
        build_update_map(child, update_map)


def main():
    if not SAVED_OBJECT_PATH.exists():
        print(f"Error: Saved object not found at {SAVED_OBJECT_PATH}")
        return

    # Load the Saved Object
    with open(SAVED_OBJECT_PATH, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    # Build the map (ID -> CustomDeck Data)
    update_map = {}

    # Saved objects usually have the main object in "ObjectStates" or are the object itself
    root_obj = saved_data.get("ObjectStates", [saved_data])[0]
    build_update_map(root_obj, update_map)

    print(f"Found {len(update_map)} unique IDs in Saved Object.")

    # Update Decomposed Files
    update_count = 0
    for json_file in PROJECT_PATH.rglob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        if file_data.get("Name") in ["Card", "CardCustom"]:
            file_id = get_metadata(json_file, file_data)
            custom_deck = file_data.get("CustomDeck")

            if file_id in update_map and custom_deck:
                deck_id = list(custom_deck.keys())[0]

                # Update the CustomDeck reference
                file_data["CustomDeck"] = {deck_id: update_map[file_id]}

                # Write back to the project folder
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(file_data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                update_count += 1

    print(f"Successfully updated {update_count} files in project.")


if __name__ == "__main__":
    main()
