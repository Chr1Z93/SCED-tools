# Copies metadata from a template file or an entire folder of files to all matching files

import os
import json
from pathlib import Path
from collections import OrderedDict

# --- Configuration ---
SEARCH_FOLDER = Path(r"C:\git\SCED-downloads\decomposed")
TEMPLATE_FOLDER = Path(r"C:\git\SCED-downloads\decomposed\campaign\Night of the Zealot")

# Set TEMPLATE_FILE to a specific path if you want to process only one template.
TEMPLATE_FILE = Path(r"")


# --- Helper Functions ---
def get_template_data(template_gmnotes_path: Path) -> dict | None:
    current_new_gmnotes_content = None
    current_filter_string_gmnotes = None
    current_target_card_name = None

    # Read and parse the template .gmnotes content as JSON
    with open(template_gmnotes_path, "r", encoding="utf-8") as f_template_gmnotes:
        current_new_gmnotes_content = f_template_gmnotes.read()

        # Attempt to load the .gmnotes content as JSON
        gmnotes_json_data = json.loads(current_new_gmnotes_content)

        # Check 'type' for Assets, Treacheries and Enemies
        template_type = gmnotes_json_data.get("type")
        if not template_type or (
            template_type != "Asset"
            and template_type != "Treachery"
            and template_type != "Enemy"
        ):
            print(
                f"Warning: {template_gmnotes_path} has type '{template_type}'. Skipping."
            )
            return None

        # Extract the 'id' field to form the filter string
        template_id = gmnotes_json_data.get("id")
        if not template_id:
            print(f"Warning: {template_gmnotes_path} has no 'id'. Skipping.")
            return None

        current_filter_string_gmnotes = f'"id": "{template_id}"'

    # Derive the corresponding JSON file and get its Nickname
    template_json_path = template_gmnotes_path.with_suffix(".json")
    if template_json_path.exists():
        with open(template_json_path, "r", encoding="utf-8") as f_json_template:
            template_json_data = json.load(f_json_template)
            current_target_card_name = template_json_data.get("Nickname")
            if not current_target_card_name:
                print(f"Warning: {template_json_path} has no 'Nickname'. Skipping.")
                return None  # Skip if no Nickname in template JSON
    else:
        print(f"Warning: JSON not found for: {template_gmnotes_path}. Skipping.")
        return None  # Skip if no corresponding JSON

    return {
        "filter_string_gmnotes": current_filter_string_gmnotes,
        "new_gmnotes_content": current_new_gmnotes_content,
        "target_card_name": current_target_card_name,
    }


def get_relative_gmnotes_path(absolute_path: Path) -> str:
    # Construct the path for the new .gmnotes file (assuming absolute_path is the .json path)
    # If absolute_path is already a .gmnotes path, this will just re-create it.
    new_gmnotes_filename = absolute_path.stem + ".gmnotes"
    new_gmnotes_path = absolute_path.parent / new_gmnotes_filename

    # Adjust relative path to start two folders deeper
    relative_to_search_folder = new_gmnotes_path.relative_to(SEARCH_FOLDER)
    path_components = relative_to_search_folder.parts
    if len(path_components) >= 3:
        return Path(*path_components[2:]).as_posix()
    else:
        return relative_to_search_folder.as_posix()


def process_target_file(file_path: Path, template_data: dict):
    current_filter_string_gmnotes = template_data["filter_string_gmnotes"]
    current_new_gmnotes_content = template_data["new_gmnotes_content"]
    current_target_card_name = template_data["target_card_name"]

    # Scenario 1: Update existing .gmnotes files
    if file_path.suffix == ".gmnotes":
        with open(file_path, "r", encoding="utf-8") as f_target:
            content = f_target.read()

        if current_filter_string_gmnotes in content:
            if current_new_gmnotes_content != content:
                with open(file_path, "w", encoding="utf-8") as f_target:
                    f_target.write(current_new_gmnotes_content)
                print(f"Updated .gmnotes:   {get_relative_gmnotes_path(file_path)}")

    # Scenario 2: Add .gmnotes to .json files without metadata
    elif file_path.suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f_json:
            json_data = json.load(f_json)

        # Check if GMNotes or GMNotes_path fields exist
        if "GMNotes" in json_data or "GMNotes_path" in json_data:
            return  # Skip if metadata already exists

        # Check for exact match of the 'Nickname' field
        if json_data.get("Nickname") != current_target_card_name:
            return  # Skip if Nickname doesn't match

        # Get the relative path for the new .gmnotes file
        relative_gmnotes_path = get_relative_gmnotes_path(file_path)

        # Construct the full path for the new .gmnotes file to write to
        new_gmnotes_filename = file_path.stem + ".gmnotes"
        new_gmnotes_path_full = file_path.parent / new_gmnotes_filename

        # Write the template content to the new .gmnotes file
        with open(new_gmnotes_path_full, "w", encoding="utf-8") as f_new_gmnotes:
            f_new_gmnotes.write(current_new_gmnotes_content)

        json_data["GMNotes_path"] = relative_gmnotes_path

        # Sort JSON fields alphabetically before writing
        sorted_json_data = OrderedDict(sorted(json_data.items()))

        # Save the updated JSON data
        with open(file_path, "w", encoding="utf-8") as f_json:
            json.dump(sorted_json_data, f_json, indent=2)
            f_json.write("\n")  # Add an empty line at the end of the file
        print(f"Added GMNotes_path: {relative_gmnotes_path}")


# --- Main Execution ---
def main():
    templates_to_process = []

    # Decide whether to use a single TEMPLATE_FILE or scan TEMPLATE_FOLDER
    if TEMPLATE_FILE.is_file():  # Check if TEMPLATE_FILE is a valid existing file
        print(f"Using single template file: {TEMPLATE_FILE}")
        template_data = get_template_data(TEMPLATE_FILE)
        if template_data:
            templates_to_process.append(template_data)
        else:
            print(f"Error: Could not prepare data for single template file. Exiting.")
            return  # Exit main if single template fails
    else:
        print(f"Scanning template folder: {TEMPLATE_FOLDER}")
        for template_root, _, template_files in os.walk(TEMPLATE_FOLDER):
            for template_file_name in template_files:
                if not template_file_name.endswith(".gmnotes"):
                    continue

                current_template_gmnotes_path = Path(template_root) / template_file_name
                template_data = get_template_data(current_template_gmnotes_path)
                if template_data:
                    templates_to_process.append(template_data)

    if not templates_to_process:
        print("No valid templates found to process. Exiting.")
        return

    # Process files in SEARCH_FOLDER for each discovered/selected template
    for template_data in templates_to_process:
        print(f"\n--- Processing with template ---")
        print(f"Template ID filter: {template_data['filter_string_gmnotes']}")
        print(f"Template Nickname: {template_data['target_card_name']}")

        for root, _, files in os.walk(SEARCH_FOLDER):
            for file_name in files:
                file_path = Path(root) / file_name
                process_target_file(file_path, template_data)

    print("\nScript finished.")


if __name__ == "__main__":
    main()
