import os
import json
from pathlib import Path
from collections import OrderedDict

# --- Config ---
search_folder = Path(r"C:\git\SCED-downloads\decomposed")
template_gmnotes_file = Path(
    r"C:\git\SCED-downloads\decomposed\campaign\Night of the Zealot\CoreNightoftheZealot.64a613\1TheGathering.667111\EncounterDeck.f98bcc\FrozeninFear.0f4202.gmnotes"
)

# For updating existing .gmnotes files
filter_string_gmnotes = '"id": "01164"'  # String to search for within .gmnotes content

# For adding new .gmnotes to .json files
target_card_name = "Frozen in Fear"  # Exact match for the 'Nickname' field in the JSON


# --- Load content from template file ---
try:
    with open(template_gmnotes_file, "r", encoding="utf-8") as f_template:
        new_gmnotes_content = f_template.read()
except FileNotFoundError:
    print(f"Error: Template .gmnotes file not found at {template_gmnotes_file}")
    exit()
except Exception as e:
    print(f"Error reading template .gmnotes file: {e}")
    exit()


# --- Process files ---
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
                    print(f"Updated existing .gmnotes: {file_path}")

        # Scenario 2: Add .gmnotes to .json files without metadata
        elif file.endswith(".json"):

            with open(file_path, "r", encoding="utf-8") as f_json:
                json_data = json.load(f_json)

            # Check if GMNotes or GMNotes_path fields exist
            if "GMNotes" in json_data or "GMNotes_path" in json_data:
                continue

            # Check for exact match of the 'Nickname' field
            if json_data.get("Nickname") != target_card_name:
                continue

            # Construct the path for the new .gmnotes file
            # It will be in the same directory as the .json file,
            # with the same name but a .gmnotes extension
            new_gmnotes_filename = file_path.stem + ".gmnotes"
            new_gmnotes_path_full = file_path.parent / new_gmnotes_filename

            # Write the template content to the new .gmnotes file
            with open(new_gmnotes_path_full, "w", encoding="utf-8") as f_new_gmnotes:
                f_new_gmnotes.write(new_gmnotes_content)

            # --- Adjust relative path to start two folders deeper ---
            # Example: C:\git\SCED-downloads\decomposed\scenario\Challenge Scenario - By the Book\BytheBook.cc7eb3\EncounterDeck.404746\FrozeninFear.0f4202.json
            # If search_folder is C:\git\SCED-downloads\decomposed
            # file_path is C:\git\SCED-downloads\decomposed\scenario\Challenge Scenario - By the Book\BytheBook.cc7eb3\EncounterDeck.404746\FrozeninFear.0f4202.json
            # We want the relative path to be "BytheBook.cc7eb3/EncounterDeck.404746/FrozeninFear.0f4202.gmnotes"

            # Get the parts of the path relative to search_folder
            relative_to_search_folder = new_gmnotes_path_full.relative_to(search_folder)

            # Split the path into parts and skip the first two (e.g., 'scenario' and 'Challenge Scenario - By the Book')
            # We take from the 3rd component onwards (index 2)
            path_components = relative_to_search_folder.parts
            if len(path_components) >= 3:
                # Join the components from the third one onwards
                adjusted_relative_gmnotes_path = Path(*path_components[2:]).as_posix()
            else:
                # If there aren't enough components to skip two, use the full relative path
                adjusted_relative_gmnotes_path = relative_to_search_folder.as_posix()

            json_data["GMNotes_path"] = adjusted_relative_gmnotes_path

            # --- Sort JSON fields alphabetically before writing ---
            # Convert to OrderedDict, sort by keys, then dump
            sorted_json_data = OrderedDict(sorted(json_data.items()))

            # Save the updated JSON data
            with open(file_path, "w", encoding="utf-8") as f_json:
                json.dump(sorted_json_data, f_json, indent=2)
                f_json.write("\n")  # Add an empty line at the end of the file
            print(f"Added GMNotes_path: {adjusted_relative_gmnotes_path}")

print("\nScript finished.")
