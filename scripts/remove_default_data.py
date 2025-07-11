import os
import json
import copy

# Define the default key-value pairs you want to remove from your JSON files.
# The script will recursively check these values. If a nested object in your
# file becomes empty after removing its default-valued keys, the entire
# object will be removed.
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

# Set the root directory where your JSON files are located.
# For example: 'C:/Users/YourUser/Documents/My Games/Tabletop Simulator/Saves'
# Use '.' to process the directory where this script is located.
TARGET_DIRECTORY = r"C:\git\SCED\objects\AdditionalPlayerCards.2cba6b"


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
        if key in defaults:
            default_value = defaults[key]
            current_value = data.get(key)

            # If the value is a dictionary, recurse into it
            if isinstance(current_value, dict) and isinstance(default_value, dict):
                remove_default_values(current_value, default_value)
                # If the nested dictionary is now empty, remove the key
                if not current_value:
                    del data[key]
            # For non-dictionary values, if they match the default, remove the key
            elif current_value == default_value:
                del data[key]


def process_files_in_directory(directory, defaults):
    """
    Walks through a directory and processes all .json files.
    """
    print(f"Starting cleanup in directory: '{os.path.abspath(directory)}'\n")
    total_files = 0
    modified_files = 0

    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(
                (".json", ".ttslua")
            ):  # Handles standard JSON and saved object files
                file_path = os.path.join(root, filename)
                total_files += 1

                print(f"-> Processing: {file_path}")
                try:
                    # Read the original file to load JSON data
                    with open(file_path, "r", encoding="utf-8-sig") as f:
                        content = f.read()
                        # TTS JSON can sometimes have leading/trailing characters
                        json_start = content.find("{")
                        json_end = content.rfind("}") + 1
                        if json_start == -1:
                            print("   - No JSON object found. Skipping.")
                            continue

                        json_content = content[json_start:json_end]
                        data = json.loads(json_content)

                    # Keep a deep copy of the original data for comparison
                    original_data = copy.deepcopy(data)

                    # Remove the default values by modifying 'data' in place
                    remove_default_values(data, defaults)

                    # If the data has changed, write it back to the file
                    if data != original_data:
                        with open(file_path, "w", encoding="utf-8") as f:
                            # Use an indent of 2 and no trailing whitespace for clean files
                            json.dump(data, f, indent=2, separators=(",", ": "))
                            # Add a newline at the end of the file
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
    if not os.path.isdir(TARGET_DIRECTORY):
        print(f"Error: The specified directory '{TARGET_DIRECTORY}' does not exist.")
    else:
        process_files_in_directory(TARGET_DIRECTORY, DEFAULT_VALUES)
