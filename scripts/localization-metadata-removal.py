# Removes all metadata except ID from GMNotes. Should be used for localizations - only ID is needed to replace
# the object, all other attributes are taken from the original object.

import os
import json
import copy

# Set the root directory where your JSON files are located.
# Examples:
# r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Russian - Player Cards\LanguagePackRussian-PlayerCards.RussianI"
# r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German - Player Cards\LanguagePackGerman-PlayerCards.GermanI"
# r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Russian - Campaigns\LanguagePackRussian-Campaigns.RussianC"
# Use "." to process the directory where this script is located.
TARGET_DIRECTORY = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Russian - Player Cards\LanguagePackRussian-PlayerCards.RussianI"

# Defines keys that should remain in the GMNotes - all keys not listed here will be deleted
KEYS_TO_KEEP = {
    "id"
}

DETAILED_PRINTING = False
PRINTING_DEPTH = 2

def process_files_in_directory(directory, keys_to_keep):
    """
    Walks through a directory and processes all .json and .gmnotes files.
    """
    abs_directory = os.path.abspath(directory)
    if not os.path.isdir(abs_directory):
        print(f"Error: The specified directory '{abs_directory}' does not exist.")
        return

    print(f"Starting cleanup in directory: '{abs_directory}'")
    total_files = 0
    modified_files = 0
    last_root = None

    for root, _, files in os.walk(directory):
        # Print a header for the subfolder if within depth limit
        if root != last_root:
            relative_path = os.path.relpath(root, abs_directory)

            # Calculate depth: root is 0, direct subfolder is 1, etc.
            if relative_path == ".":
                depth = 0
            else:
                depth = len(relative_path.split(os.sep))

            # depth > 0 ensures we don't re-print the starting directory.
            if 0 < depth <= PRINTING_DEPTH:
                print(f"Processing subfolder: {root}")
            last_root = root

        for filename in files:
            # Handles standard JSON and GMNotes files
            if filename.endswith(".json") or filename.endswith(".gmnotes"):
                file_path = os.path.join(root, filename)
                total_files += 1

                if DETAILED_PRINTING:
                    print(f"-> Processing: {file_path}")
                try:
                    # Read the original file to load JSON data
                    # Using utf-8-sig to handle potential BOM (Byte Order Mark)
                    with open(file_path, "r", encoding="utf-8-sig") as f:
                        content = f.read()
                        # TTS JSON can sometimes have leading/trailing characters; we find the main object
                        json_start = content.find("{")
                        json_end = content.rfind("}") + 1
                        if json_start == -1:
                            print("   - No JSON object found. Skipping.")
                            continue

                        json_content = content[json_start:json_end]
                        data = json.loads(json_content)

                    # Keep a deep copy of the original data for comparison later
                    original_data = copy.deepcopy(data)

                    # Get GMNotes object from JSON (if it exists) and modify it in-place
                    if filename.endswith(".json"):
                        if "GMNotes" in data:
                            gmnotes = json.loads(data["GMNotes"])
                            for key in list(gmnotes.keys()):
                                if key not in keys_to_keep:
                                    del gmnotes[key]
                            data["GMNotes"] = json.dumps(gmnotes, indent=2)

                    # Get GMNotes object from file and modify it in-place
                    if filename.endswith(".gmnotes"):
                        for key in list(data.keys()):
                            if key not in keys_to_keep:
                                del data[key]

                    # We rewrite the file if data was changed OR if the original file
                    # contained Unicode escape sequences that need to be fixed.
                    file_needs_rewrite = (data != original_data) or (
                        "\\u" in json_content
                    )

                    if file_needs_rewrite:
                        with open(file_path, "w", encoding="utf-8") as f:
                            # Use an indent of 2 and no trailing whitespace for clean files
                            json.dump(
                                data,
                                f,
                                indent=2,
                                separators=(",", ": "),
                                ensure_ascii=False,
                            )
                            # Add a newline at the end of the file for POSIX compliance
                            f.write("\n")

                        modified_files += 1

                        if DETAILED_PRINTING:
                            print("   - ✅ Modified and saved.")
                    else:
                        if DETAILED_PRINTING:
                            print("   - 💤 No changes needed.")

                except json.JSONDecodeError:
                    print(f"   - ⚠️ Error: Could not decode JSON. ({file_path})")
                except Exception as e:
                    print(f"   - ❌ An unexpected error occurred: {e}. ({file_path})")

    print("\n--- ✨ Cleanup Complete! ---")
    print(f"Scanned {total_files} files.")
    print(f"Modified {modified_files} files.")


if __name__ == "__main__":
    process_files_in_directory(TARGET_DIRECTORY, KEYS_TO_KEEP)
