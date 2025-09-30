# This script will process deck objects and make sure duplicate cards are only stored once.
# It will optionally sort the deck in reverse alphabetical order too.
# Act / Agenda deck will be skipped.

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Set the root folder path containing the JSON files
ROOT_FOLDER_PATH = r"C:\git\SCED-downloads\decomposed\campaign\The Forgotten Age\TheForgottenAge.0bcf19\2TheDoomofEztli.065ce1"

# If set to True, the key order in the resulting JSON file will be preserved
PRESERVE_KEY_ORDER = False


def clean_and_sort_deck(
    data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Set[str]]:
    """
    1. Creates a DeckID <-> ContainedObject link map.
    2. Conditionally sorts the ContainedObjects list (unless PRESERVE_KEY_ORDER is True).
    3. Reorders the DeckIDs list to match the new ContainedObjects order.
    4. Deduplicates DeckIDs: keeps the alphabetically FIRST filename for duplicates
       and identifies the files (ContainedObjects) that need to be discarded.

    Returns the updated data dictionary and a set of filenames to be deleted.
    """
    contained_objects: List[str] = data.get("ContainedObjects_order", [])
    deck_ids: List[str] = data.get("DeckIDs", [])

    if len(contained_objects) != len(deck_ids):
        print(
            f"Warning: List lengths mismatch ({len(contained_objects)} vs {len(deck_ids)}). Skipping sort/dedupe."
        )
        return data, set()

    # Create the original mapping
    original_mapping = {
        obj: deck_id for obj, deck_id in zip(contained_objects, deck_ids)
    }

    # --- Conditional List Sorting ---
    if PRESERVE_KEY_ORDER:
        # If preserving list order, use original lists directly.
        new_contained_objects = contained_objects
        new_deck_ids = deck_ids
    else:
        # Default mode: Sort ContainedObjects in reverse alphabetical order
        new_contained_objects = sorted(contained_objects, reverse=True)

        # Reorder DeckIDs to maintain the link
        new_deck_ids = [original_mapping[obj] for obj in new_contained_objects]

    # --- Deduplication Logic ---

    # Map DeckID to all associated filenames (ContainedObjects)
    deck_id_to_objects: Dict[str, List[str]] = {}
    for obj, deck_id in zip(new_contained_objects, new_deck_ids):
        deck_id_to_objects.setdefault(deck_id, []).append(obj)

    discarded_files: Set[str] = set()
    keeper_mapping: Dict[str, str] = (
        {}
    )  # Map from discarded filename to keeper filename

    # Identify keepers and discards
    for deck_id, files in deck_id_to_objects.items():
        if len(files) > 1:
            # The "keeper" is the alphabetically first filename
            keeper_file = min(files)

            for file in files:
                if file != keeper_file:
                    discarded_files.add(file)
                    # For all duplicate entries pointing to this deck_id,
                    # the file pointer in the list must be updated to the keeper file.
                    keeper_mapping[file] = keeper_file

    # Apply keeper mapping to the new ContainedObjects list
    # The 'DeckIDs' list remains unchanged, as we only update the file pointers.
    final_contained_objects = []
    for obj in new_contained_objects:
        # If the filename is a discarded file, use its keeper instead
        final_contained_objects.append(keeper_mapping.get(obj, obj))

    # Final list updates
    data["ContainedObjects_order"] = final_contained_objects
    data["DeckIDs"] = new_deck_ids

    return data, discarded_files


def delete_discarded_files(discarded_files: Set[str], associated_folder_path: Path):
    """Deletes the .json and .gmnotes files for all discarded filenames from the associated subfolder."""
    if not discarded_files:
        return

    print(f"Cleaning up {len(discarded_files)} discarded files...")

    for filename_stem in discarded_files:
        # 1. Delete the .json file
        json_file = associated_folder_path / f"{filename_stem}.json"
        if json_file.exists():
            json_file.unlink()
            print(f"  -> Deleted: {json_file.name}")

        # 2. Delete the .gmnotes file if it exists
        gmnotes_file = associated_folder_path / f"{filename_stem}.gmnotes"
        if gmnotes_file.exists():
            gmnotes_file.unlink()
            print(f"  -> Deleted: {gmnotes_file.name}")


def process_folder_for_cleanup(root_folder_path: str):
    """Main function to iterate through the root folder, validate files, and run the cleanup and sorting logic."""
    print(f"Starting deck cleanup process in folder: {root_folder_path}\n")

    root_path = Path(root_folder_path)
    if not root_path.is_dir():
        print(f"Error: Root folder not found at {root_folder_path}")
        return

    # Loop through all .json files in that folder
    for main_json_path in root_path.glob("*.json"):
        print(f"Processing {main_json_path.name}")

        # Check for accompanying folder
        folder_name = main_json_path.stem
        associated_folder_path = root_path / folder_name

        if not associated_folder_path.is_dir():
            continue

        # Load the JSON file
        with open(main_json_path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)

        # Check for required keys
        if "ContainedObjects_order" not in data or not "DeckIDs" in data:
            continue

        # Skip Act / Agenda based on Nickname
        if "Nickname" in data and (
            "act deck" in data["Nickname"].lower()
            or "agenda deck" in data["Nickname"].lower()
        ):
            print("  Skipping: Detected as Act/Agenda deck.")
            continue

        print("  Required keys found. Performing sort and deduplication.")

        # Capture the original key order before any modification to data
        original_keys = list(data.keys())

        # Perform the sorting and deduplication
        updated_data, discarded_files = clean_and_sort_deck(data)

        # Delete the discarded files
        delete_discarded_files(discarded_files, associated_folder_path)

        # Save the updated JSON file (preserving top-level keys in the original order)
        ordered_data = {
            key: updated_data[key] for key in original_keys if key in updated_data
        }

        json_output = (
            json.dumps(ordered_data, indent=2, sort_keys=False, ensure_ascii=False)
            + "\n"
        )

        # Check if the content has actually changed
        current_content = main_json_path.read_text(encoding="utf-8")

        if current_content == json_output:
            # Content is identical, skip writing to avoid file modification date changes
            print(f"  Skipped saving {main_json_path.name}: No changes detected.")
            continue

        # Content has changed, proceed with saving
        with open(main_json_path, "w", encoding="utf-8") as f:
            f.write(json_output)

        if PRESERVE_KEY_ORDER:
            print(f"  Saved {main_json_path.name}: Kept card order.")
        else:
            print(f"  Saved {main_json_path.name}: Sorted cards alphabetically.")

        print("-" * 30)


if __name__ == "__main__":
    # Execute the main function with the configured path
    process_folder_for_cleanup(ROOT_FOLDER_PATH)
