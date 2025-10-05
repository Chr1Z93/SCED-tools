# TTS saves include a lot of data that matches the default value
# If such a field is missing, TTS will load the default value either way
# So they can be safely removed to minimize file size and improve performance.

import os
import json
import copy
import math

# Set the root directory where your JSON files are located.
# Examples:
# r"C:\git\SCED\objects"
# r"C:\git\SCED\objects\AdditionalPlayerCards.2cba6b"
# r"C:\git\SCED-downloads\decomposed"
# Use "." to process the directory where this script is located.
TARGET_DIRECTORY = r"C:\git\SCED-downloads"

DETAILED_PRINTING = True
PRINTING_DEPTH = 2

# Default key-value pairs to remove from the JSON files.
# If a key's value in a file matches the default, the key will be removed.
DEFAULT_VALUES = {
    "AltLookAngle": {"x": 0, "y": 0, "z": 0},
    "Autoraise": True,
    "Bag": {"Order": 0},
    "ColorDiffuse": {"r": 0.71324, "g": 0.71324, "b": 0.71324},
    "CustomMesh": {
        "NormalURL": "",
        "ColliderURL": "",
        "Convex": True,
        "CastShadows": True,
    },
    # This does NOT match the default value but it is superfluous either way
    "PhysicsMaterial": {
        "StaticFriction": 0.6,
        "DynamicFriction": 0.6,
        "Bounciness": 0.0,
        "FrictionCombine": 0,
        "BounceCombine": 0,
    },
    # This does NOT match the default value but it is superfluous either way
    "Rigidbody": {"Mass": 1.375, "Drag": 5.0, "AngularDrag": 5.0, "UseGravity": True},
    "Description": "",
    "DragSelectable": True,
    "GMNotes": "",
    "Grid": True,
    "GridProjection": False,
    "Hands": True,
    "HideWhenFaceDown": True,
    "IgnoreFoW": False,
    "LayoutGroupSortIndex": 0,
    "Locked": False,
    "LuaScript": "",
    "LuaScriptState": "",
    "MaterialIndex": -1,
    "MeasureMovement": False,
    "MeshIndex": -1,
    "Number": 0,
    "SidewaysCard": False,
    "Snap": True,
    "Sticky": True,
    "Tooltip": True,
    "Value": 0,
    "XmlUI": "",
}


def remove_default_values(data, defaults, is_nested=False):
    """
    Recursively removes keys from a dictionary if their values match the defaults.
    Also handles special cases for "Deck" objects and float precision.
    Removes position keys from any 'Transform' dictionary found
    when is_nested is True (i.e., not the top-level object in the file).
    This function modifies the 'data' dictionary in place.

    Args:
        data (dict): The dictionary to clean (from the JSON file).
        defaults (dict): The dictionary of default values.
        is_nested (bool, optional): True if the current data is nested
                                    within the main file object. Defaults to False.
    """
    # Special case: If the object's Name is "Deck", remove "HideWhenFaceDown" field
    if data.get("Name") == "Deck" and "HideWhenFaceDown" in data:
        del data["HideWhenFaceDown"]

    # Remove position keys from 'Transform' if this object is nested (not top-level).
    if is_nested and "Transform" in data:
        transform_data = data["Transform"]
        if isinstance(transform_data, dict):
            for pos_key in ["posX", "posY", "posZ"]:
                if pos_key in transform_data:
                    del transform_data[pos_key]

    # Iterate over a copy of the keys, as we may modify the dictionary
    for key in list(data.keys()):
        current_value = data.get(key)

        # Case 1: The key is a defined default (e.g., "AltLookAngle").
        if key in defaults:
            default_value = defaults[key]

            # Special handling for "ColorDiffuse" to account for float precision.
            if (
                key == "ColorDiffuse"
                and isinstance(current_value, dict)
                and all(k in current_value for k in ("r", "g", "b"))
            ):
                precision = 5  # Precision based on the default value
                # Using math.isclose is robust for float comparisons
                if (
                    math.isclose(
                        current_value["r"],
                        default_value["r"],
                        rel_tol=1e-9,
                        abs_tol=10**-precision,
                    )
                    and math.isclose(
                        current_value["g"],
                        default_value["g"],
                        rel_tol=1e-9,
                        abs_tol=10**-precision,
                    )
                    and math.isclose(
                        current_value["b"],
                        default_value["b"],
                        rel_tol=1e-9,
                        abs_tol=10**-precision,
                    )
                ):
                    del data[key]

            # Special handling for "CustomMesh" to remove nested defaults.
            elif key == "CustomMesh" and isinstance(current_value, dict):
                # Iterate over a copy of the nested keys
                for mesh_key in list(current_value.keys()):
                    if (
                        mesh_key in default_value
                        and current_value[mesh_key] == default_value[mesh_key]
                    ):
                        del current_value[mesh_key]
                # If the CustomMesh dictionary becomes empty after cleanup, remove it.
                if not current_value:
                    del data[key]

            # Standard comparison for all other keys.
            elif current_value == default_value:
                del data[key]

        # Do not recurse into "AttachedDecals"
        elif key == "AttachedDecals":
            continue

        # Case 2: The key is NOT a default, but its value is a dictionary.
        # We should step into it to clean its contents recursively.
        elif isinstance(current_value, dict):
            # Pass True to indicate that the next level is nested.
            remove_default_values(current_value, defaults, is_nested=True)

        # Case 3: The key is NOT a default, but its value is a list.
        # We check for any dictionaries within the list to clean them.
        # This is common for structures like "ObjectStates" in TTS files.
        elif isinstance(current_value, list):
            for item in current_value:
                if isinstance(item, dict):
                    # Pass True to indicate that items in the list are nested.
                    remove_default_values(item, defaults, is_nested=True)


def is_tts_object_folder(folder_name):
    """
    Checks if a folder name matches the TTS decomposed object pattern:
    e.g., "ObjectName.GUID" (two parts separated by a dot, no spaces).
    """
    # Split the name by the dot.
    parts = folder_name.split(".")

    # Must have exactly two parts.
    if len(parts) != 2:
        return False

    # Check that neither part contains a space, and both are non-empty.
    # The TTS GUID part is typically a short hexadecimal string.
    if " " in parts[0] or " " in parts[1] or not parts[0] or not parts[1]:
        return False

    return True


def process_files_in_directory(directory, defaults):
    """Walks through a directory and processes all .json files."""
    abs_directory = os.path.abspath(directory)
    if not os.path.isdir(abs_directory):
        print(f"Error: The specified directory '{abs_directory}' does not exist.")
        return

    print(f"Starting cleanup in directory: '{abs_directory}'")
    total_files = 0
    modified_files = 0
    last_root = None

    for root, dirs, files in os.walk(directory):
        if ".git" in dirs:
            dirs.remove(".git")

        if ".vscode" in dirs:
            dirs.remove(".vscode")

        # Determine if the *current file* should be treated as nested based on its containing folder.
        is_folder_nested = is_tts_object_folder(os.path.basename(root))

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
            # Handles standard JSON and Tabletop Simulator saved object files
            if filename.endswith(".json"):
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

                    # Remove the default values by modifying 'data' in place
                    remove_default_values(data, defaults, is_nested=is_folder_nested)

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
    process_files_in_directory(TARGET_DIRECTORY, DEFAULT_VALUES)
