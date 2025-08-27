# Moves metadata inline if it is short enough

import os
import json
from pathlib import Path
from collections import OrderedDict

# --- Configuration ---
SEARCH_FOLDER = Path(
    r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German - Player Cards\LanguagePackGerman-PlayerCards.GermanI"
)
MAX_CHARACTERS = 80  # The maximum character count for the GMNotes content


# --- Main Logic ---
def main():
    """
    Loops through all .json files and embeds GMNotes content if it's short enough.
    Assumes the .gmnotes file is in the same folder with the same base name.
    """
    print(f"Scanning folder: {SEARCH_FOLDER}")
    print(f"Maximum allowed GMNotes character count: {MAX_CHARACTERS} characters")

    for root, dirs, files in os.walk(SEARCH_FOLDER):
        if ".git" in dirs:
            dirs.remove(".git")

        if ".vscode" in dirs:
            dirs.remove(".vscode")

        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            file_path = Path(root) / file_name

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Warning: Could not decode JSON file {file_path}. Error: {e}")
                continue

            # Check for the "GMNotes_path" field
            gmnotes_path_str = json_data.get("GMNotes_path")
            if not gmnotes_path_str:
                continue

            # Construct the path to the .gmnotes file in the same directory
            gmnotes_path = file_path.with_suffix(".gmnotes")

            if not gmnotes_path.exists():
                print(f"Warning: .gmnotes file not found for {file_path}.")
                continue

            # Read the content of the .gmnotes file
            with open(gmnotes_path, "r", encoding="utf-8") as f_gmnotes:
                gmnotes_content = f_gmnotes.read()

            # Check the character count of the content
            if len(gmnotes_content) <= MAX_CHARACTERS:
                # Delete the .gmnotes file
                os.remove(gmnotes_path)

                # Add the content as a new "GMNotes" field
                json_data["GMNotes"] = gmnotes_content

                # Delete the old "GMNotes_path" field
                del json_data["GMNotes_path"]

                # Sort JSON fields alphabetically before writing
                sorted_json_data = OrderedDict(sorted(json_data.items()))

                # Write the updated JSON back to the file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(sorted_json_data, f, indent=2)
                    f.write("\n")  # Add an empty line at the end

    print("\nScript finished.")


if __name__ == "__main__":
    main()
