import os
import json
import copy

# Set the root directory where your JSON files are located.
# For example: r'C:\git\SCED\objects'
# Use '.' to process the directory where this script is located.
TARGET_DIRECTORY = r"C:\git\SCED\objects\AdditionalPlayerCards.2cba6b"

# Define the default key-value pairs you want to remove from your JSON files.
# The script will check these values. If a key's value in your file
# matches the default, the key will be removed.
DEFAULT_VALUES = {
    "AltLookAngle": {"x": 0, "y": 0, "z": 0},
    "Autoraise": True,
    "ColorDiffuse": {"r": 0.71324, "g": 0.71324, "b": 0.71324},
    "Description": "",
    "DragSelectable": True,
    "Grid": True,
    "GridProjection": False,
    "Hands": True,
    "HideWhenFaceDown": True,
    "IgnoreFoW": False,
    "LayoutGroupSortIndex": 0,
    "Locked": False,
    "LuaScript": "",
    "LuaScriptState": "",
    "MeasureMovement": False,
    "SidewaysCard": False,
    "Snap": True,
    "Sticky": True,
    "Tooltip": True,
    "Value": 0,
    "XmlUI": "",
}


def remove_default_values(data, defaults):
    """
    Recursively removes keys from a dictionary if their values match the defaults.
    This function modifies the 'data' dictionary in place.

    Args:
        data (dict): The dictionary to clean (from the JSON file).
        defaults (dict): The dictionary of default values.
    """
    # Iterate over a copy of the keys, as we may modify the dictionary
    for key in list(data.keys()):
        current_value = data.get(key)

        # Case 1: The key is a defined default (e.g., "AltLookAngle").
        # We compare the entire value directly.
        if key in defaults:
            # If the current value is identical to the default value, remove the key.
            # This works for simple types (True, 0, "") and for entire dictionaries
            # (e.g., {"x": 0, "y": 0, "z": 0}).
            if current_value == defaults[key]:
                del data[key]

        # Case 2: The key is NOT a default, but its value is a dictionary.
        # We should step into it to clean its contents recursively.
        elif isinstance(current_value, dict):
            remove_default_values(current_value, defaults)

        # Case 3: The key is NOT a default, but its value is a list.
        # We check for any dictionaries within the list to clean them.
        # This is common for structures like "ObjectStates" in TTS files.
        elif isinstance(current_value, list):
            for item in current_value:
                if isinstance(item, dict):
                    remove_default_values(item, defaults)


def process_files_in_directory(directory, defaults):
    """
    Walks through a directory and processes all .json files.
    """
    abs_directory = os.path.abspath(directory)
    if not os.path.isdir(abs_directory):
        print(f"Error: The specified directory '{abs_directory}' does not exist.")
        return

    print(f"Starting cleanup in directory: '{abs_directory}'\n")
    total_files = 0
    modified_files = 0

    for root, _, files in os.walk(directory):
        for filename in files:
            # Handles standard JSON and Tabletop Simulator saved object files
            if filename.endswith((".json")):
                file_path = os.path.join(root, filename)
                total_files += 1

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

                    # Remove the default values by modifying 'data' in place
                    remove_default_values(data, defaults)

                    # If the data has changed, write it back to the file
                    if data != original_data:
                        with open(file_path, "w", encoding="utf-8") as f:
                            # Use an indent of 2 and no trailing whitespace for clean files
                            json.dump(data, f, indent=2, separators=(",", ": "))
                            # Add a newline at the end of the file for POSIX compliance
                            f.write("\n")
                        print("   - ✅ Modified and saved.")
                        modified_files += 1
                    else:
                        print("   - 💤 No changes needed.")

                except json.JSONDecodeError:
                    print(f"   - ⚠️ Error: Could not decode JSON. Skipping.")
                except Exception as e:
                    print(f"   - ❌ An unexpected error occurred: {e}. Skipping.")

    print("\n--- ✨ Cleanup Complete! ---")
    print(f"Scanned {total_files} files.")
    print(f"Modified {modified_files} files.")


if __name__ == "__main__":
    process_files_in_directory(TARGET_DIRECTORY, DEFAULT_VALUES)
