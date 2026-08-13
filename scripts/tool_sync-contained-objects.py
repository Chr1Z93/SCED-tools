import json
from pathlib import Path
from typing import List, Any
from tool_gui import ToolGUI

# Setup for the GUI
OPTIONS = {
    "input_folder": {
        "type": "folder",
        "label": "Input folder",
        "default": r"C:\git\SCED\objects",
    },
    "input_file": {
        "type": "file",
        "label": "Input file",
        "default": r"C:\git\SCED\objects\AllPlayerCards.15bb07.json",
    },
}


def get_contained_file_names(folder_path: Path) -> List[str]:
    """
    Lists all json files within the given folder, stripping their file extensions.
    The list is sorted in reverse alphabetical order since TTS displays it in reverse.
    """
    file_names = []

    # Iterate over all items in the directory
    for item in folder_path.iterdir():
        if item.is_file() and item.suffix.lower() == ".json":
            file_names.append(item.stem)

    # Sort the list in reverse alphabetical order
    file_names.sort(reverse=True)
    return file_names


def process_json_contained_objects(log, main_json_path: Path) -> bool:
    """
    Parses the main JSON file, determines the associated folder, lists and sorts
    the contained files, updates the 'ContainedObjects_order' key, and saves the
    updated JSON file with alphabetically sorted keys and a trailing newline.
    """
    # Check if the main JSON file exists
    if not main_json_path.is_file():
        log(f"Skipped: Main JSON file not found: '{main_json_path}'")
        return False

    # Determine the associated folder path
    # The folder name is the JSON filename without the final extension (.json)
    # e.g., 'DerPfadnachCarcosa.6ad5dd.json' -> 'DerPfadnachCarcosa.6ad5dd'
    folder_name = main_json_path.stem
    associated_folder_path = main_json_path.parent / folder_name

    if not associated_folder_path.is_dir():
        log(f"Skipped: Associated folder not found: '{associated_folder_path}'")
        return False

    # Get the list of file names from the associated folder
    contained_objects_list = get_contained_file_names(associated_folder_path)
    log(f"Found {len(contained_objects_list)} json files.")

    # Parse the JSON file
    with open(main_json_path, "r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    # Update the 'ContainedObjects_order' key
    data["ContainedObjects_order"] = contained_objects_list

    # Save the file: keys sorted alphabetically and ending with a newline
    with open(main_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")

    log(f"Successfully updated 'ContainedObjects_order'")
    return True


def rebuild_contained_objects(log, folder_path: Path, file_path: Path) -> None:
    files_to_process = set()

    if file_path.is_file() and file_path.suffix.lower() == ".json":
        files_to_process.add(file_path)

    if folder_path.is_dir():
        files_to_process.update(
            entry
            for entry in folder_path.iterdir()
            if entry.is_file() and entry.suffix.lower() == ".json"
        )

    processed = 0
    failed = 0

    for path in sorted(files_to_process):
        log(f"Processing file: '{path}'")
        if process_json_contained_objects(log, path):
            processed += 1
        else:
            failed += 1

    log(f"Finished: {processed} processed, {failed} failed.")


def run_tool(config, log):
    folder_path = Path(config["input_folder"])
    file_path = Path(config["input_file"])
    rebuild_contained_objects(log, folder_path, file_path)


if __name__ == "__main__":
    ToolGUI("Sync Contained Objects", OPTIONS, run_tool).show()
