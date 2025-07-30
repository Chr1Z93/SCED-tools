import os
import json
from pathlib import Path
from collections import OrderedDict

# --- Config ---
search_folder = Path(r"C:\git\SCED-downloads\decomposed")
template_folder = Path(r"C:\git\SCED-downloads\decomposed\campaign\Night of the Zealot")

# For updating existing .gmnotes files and discovering template
filter_string_gmnotes = '"id": "01161"'

# target_card_name will be determined automatically from the template's JSON
target_card_name = None
template_gmnotes = None
new_gmnotes_content = None

# --- Discover template .gmnotes file and derive target_card_name ---
print(f"Searching for template .gmnotes file")

for root, _, files in os.walk(template_folder):
    for file in files:
        if not file.endswith(".gmnotes"):
            continue

        current_gmnotes_path = Path(root) / file
        with open(current_gmnotes_path, "r", encoding="utf-8") as f_template_gmnotes:
            content = f_template_gmnotes.read()
            if not filter_string_gmnotes in content:
                continue

            template_gmnotes = current_gmnotes_path
            new_gmnotes_content = content  # Load the content directly here
            print(f"Found template .gmnotes file: {template_gmnotes}")

            # Now, derive the corresponding JSON file and get its Nickname
            template_json_path = current_gmnotes_path.with_suffix(".json")
            if template_json_path.exists():
                with open(template_json_path, "r", encoding="utf-8") as f_json_template:
                    template_json_data = json.load(f_json_template)
                    target_card_name = template_json_data.get("Nickname")
                    if target_card_name:
                        print(f"Detected target_card_name")
                    else:
                        print(f"Warning: Template JSON has no 'Nickname' field")
            else:
                print(f"Warning: Corresponding JSON file not found")
            break  # Found the template, exit inner loop
    if template_gmnotes:
        break  # Found the template, exit outer loop

if not template_gmnotes or not target_card_name:
    if not template_gmnotes:
        print(f"Error: No template .gmnotes file found.")
    elif not target_card_name:
        print(f"Error: Could not determine target_card_name.")
    exit()

if not new_gmnotes_content:
    exit()

# --- Process files in the main search_folder ---
for root, _, files in os.walk(search_folder):
    for file in files:
        file_path = Path(root) / file

        # Scenario 1: Update existing .gmnotes files
        if file.endswith(".gmnotes"):
            with open(file_path, "r", encoding="utf-8") as f_target:
                content = f_target.read()

            if filter_string_gmnotes in content:
                if new_gmnotes_content != content:
                    with open(file_path, "w", encoding="utf-8") as f_target:
                        f_target.write(new_gmnotes_content)
                    print(f"Updated .gmnotes: {file_path}")

        # Scenario 2: Add .gmnotes to .json files without metadata
        elif file.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f_json:
                json_data = json.load(f_json)

            # Check if GMNotes or GMNotes_path fields exist
            if "GMNotes" in json_data or "GMNotes_path" in json_data:
                continue  # Skip if metadata already exists

            # Check for exact match of the 'Nickname' field
            if json_data.get("Nickname") != target_card_name:
                continue  # Skip if Nickname doesn't match

            # Construct the path for the new .gmnotes file
            new_gmnotes_filename = file_path.stem + ".gmnotes"
            new_gmnotes_path_full = file_path.parent / new_gmnotes_filename

            # Write the template content to the new .gmnotes file
            with open(new_gmnotes_path_full, "w", encoding="utf-8") as f_new_gmnotes:
                f_new_gmnotes.write(new_gmnotes_content)

            # --- Adjust relative path to start two folders deeper ---
            # Get the parts of the path relative to search_folder
            relative_to_search_folder = new_gmnotes_path_full.relative_to(search_folder)

            # Split the path into parts and skip the first two
            path_components = relative_to_search_folder.parts
            if len(path_components) >= 3:
                adjusted_relative_gmnotes_path = Path(*path_components[2:]).as_posix()
            else:
                adjusted_relative_gmnotes_path = relative_to_search_folder.as_posix()

            json_data["GMNotes_path"] = adjusted_relative_gmnotes_path

            # --- Sort JSON fields alphabetically before writing ---
            sorted_json_data = OrderedDict(sorted(json_data.items()))

            # Save the updated JSON data
            with open(file_path, "w", encoding="utf-8") as f_json:
                json.dump(sorted_json_data, f_json, indent=2)
                f_json.write("\n")  # Add an empty line at the end of the file
            print(f"Added GMNotes_path: {adjusted_relative_gmnotes_path}")

print("\nScript finished.")
