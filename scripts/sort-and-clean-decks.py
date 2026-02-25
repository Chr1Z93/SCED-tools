# This script will process deck objects and make sure duplicate cards are only stored once.
# It will optionally sort the deck in reverse alphabetical order too.
# Act / Agenda deck will be skipped.

import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Set the root folder path containing the JSON files
ROOT_FOLDER_PATH = r"C:\git\SCED-downloads\decomposed\campaign\Return to The Circle Undone"

# If set to True, the key order in the resulting JSON file will be preserved
PRESERVE_CARD_ORDER = True


def global_shallow_fix(root_path: Path):
    """
    Iterates through EVERY json file in the tree.
    Ensures CardID matches the first key in CustomDeck.
    """
    for file_path in root_path.rglob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Only process Card objects
            if data.get("Name") not in ["Card", "CardCustom"]:
                continue

            custom_deck = data.get("CustomDeck")
            if not custom_deck or "CardID" not in data:
                continue

            current_deck_id = list(custom_deck.keys())[0]
            current_card_id = data["CardID"]

            # Use zfill to ensure the index is always two digits (e.g., 05 instead of 5)
            suffix = str(current_card_id).zfill(2)[-2:]
            proper_card_id = int(f"{current_deck_id}{suffix}")

            if current_card_id != proper_card_id:
                data["CardID"] = proper_card_id
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                print(f"  -> Fixed CardID: {file_path.name}")

        except (json.JSONDecodeError, KeyError, IndexError):
            continue


def rebuild_deck_data(
    data: Dict[str, Any], associated_folder_path: Path
) -> Dict[str, Any]:
    """Handles remapping and deduplication for decks."""
    new_deck_ids = []
    canonical_custom_decks = {}  # (FaceURL, BackURL) -> canonical_id_str
    id_redirection_map = {}  # original_id_str -> canonical_id_str

    contained_objects = data.get("ContainedObjects_order", [])

    # Pass 1: Build the redirection map from current card states
    for filename_stem in contained_objects:
        card_path = associated_folder_path / f"{filename_stem}.json"
        if not card_path.exists():
            continue

        with open(card_path, "r", encoding="utf-8") as f:
            card_json = json.load(f)

        custom_deck = card_json.get("CustomDeck", {})
        if not custom_deck:
            continue

        current_deck_id = list(custom_deck.keys())[0]
        deck_info = custom_deck[current_deck_id]
        fingerprint = (deck_info.get("FaceURL"), deck_info.get("BackURL"))

        if fingerprint not in canonical_custom_decks:
            canonical_custom_decks[fingerprint] = current_deck_id
            id_redirection_map[current_deck_id] = current_deck_id
        else:
            id_redirection_map[current_deck_id] = canonical_custom_decks[fingerprint]

    # Pass 2: Consolidate card files and rebuild master Deck object
    final_custom_deck_registry = {}

    for filename_stem in contained_objects:
        card_path = associated_folder_path / f"{filename_stem}.json"
        if not card_path.exists():
            continue

        with open(card_path, "r", encoding="utf-8") as f:
            card_json = json.load(f)

        custom_deck = card_json.get("CustomDeck", {})
        current_deck_id = list(custom_deck.keys())[0]
        canonical_id = id_redirection_map.get(current_deck_id, current_deck_id)

        # Apply remapping if this is a duplicate deck
        if canonical_id != current_deck_id:
            suffix = str(card_json["CardID"]).zfill(2)[-2:]
            card_json["CardID"] = int(f"{canonical_id}{suffix}")
            card_json["CustomDeck"] = {canonical_id: custom_deck[current_deck_id]}

            with open(card_path, "w", encoding="utf-8") as f:
                json.dump(card_json, f, indent=2, ensure_ascii=False)
                f.write("\n")

        new_deck_ids.append(card_json["CardID"])
        if canonical_id not in final_custom_deck_registry:
            final_custom_deck_registry[canonical_id] = card_json["CustomDeck"][
                canonical_id
            ]

    data["DeckIDs"] = new_deck_ids
    data["CustomDeck"] = {
        k: final_custom_deck_registry[k]
        for k in sorted(final_custom_deck_registry.keys(), key=int)
    }
    return data


def clean_and_sort_deck(
    data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Set[str]]:
    """
    1. Creates a DeckID <-> ContainedObject link map.
    2. Conditionally sorts the ContainedObjects list (unless PRESERVE_CARD_ORDER is True).
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
    if PRESERVE_CARD_ORDER:
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

    # Map from discarded filename to keeper filename
    keeper_mapping: Dict[str, str] = {}

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


def process_folder_for_cleanup(root_folder_path: Path):
    """Main function to iterate through the root folder, validate files, and run the cleanup and sorting logic."""
    if not root_folder_path.is_dir():
        print(f"Error: Root folder not found at {root_folder_path}")
        return

    # Loop through all .json files in that folder
    for main_json_path in root_folder_path.glob("*.json"):
        # Check for accompanying folder
        folder_name = main_json_path.stem
        associated_folder_path = root_folder_path / folder_name

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
            continue

        # Capture the original key order before any modification to data
        original_keys = list(data.keys())

        # Perform the sorting and deduplication
        updated_data, discarded_files = clean_and_sort_deck(data)

        # Ensure correct deck data by rebuilding it
        updated_data = rebuild_deck_data(updated_data, associated_folder_path)

        # Delete the discarded files
        delete_discarded_files(discarded_files, associated_folder_path)

        # Save the updated JSON file (preserving top-level keys in the original order)
        # We ensure 'CustomDeck' is included in the output even if it wasn't there originally
        if "CustomDeck" not in original_keys:
            original_keys.append("CustomDeck")

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
            continue

        # Content has changed, proceed with saving
        with open(main_json_path, "w", encoding="utf-8") as f:
            f.write(json_output)

        if PRESERVE_CARD_ORDER:
            print(f"  Updated {main_json_path.name}: Kept card order.")
        else:
            print(f"  Updated {main_json_path.name}: Sorted cards alphabetically.")

        print("-" * 30)


def cleanup_everything(root_path):
    path = Path(root_path)

    global_shallow_fix(path)

    # Process the root folder itself
    process_folder_for_cleanup(path)

    # Iterate through every sub-directory in the tree
    for folder in path.rglob("**/"):
        process_folder_for_cleanup(folder)


if __name__ == "__main__":
    # Execute the main function with the configured path
    cleanup_everything(ROOT_FOLDER_PATH)
