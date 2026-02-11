import json

# Keys you want to remove
KEYS_TO_REMOVE = {"LuaScript", "LuaScriptState", "XmlUI", "CustomUIAssets"}

# File paths
INPUT_FILE = r"Investigators.json"
OUTPUT_FILE = r"Investigators_clean.json"

def remove_keys_recursive(data, keys_to_remove):
    """Recursively removes specified keys from a nested dictionary or list."""
    if isinstance(data, dict):
        # Build a new dictionary excluding the keys to remove
        new_dict = {}
        for k, v in data.items():
            if k not in keys_to_remove:
                # Recursively process the value and add the key/value pair
                new_dict[k] = remove_keys_recursive(v, keys_to_remove)
        return new_dict

    elif isinstance(data, list):
        # Process each item in the list recursively
        return [remove_keys_recursive(item, keys_to_remove) for item in data]

    else:
        # Return scalar types (int, str, bool, etc.) as is
        return data


try:
    # 1. Read the JSON file
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    print(f"Successfully loaded data from {INPUT_FILE}")

    # 2. Clean the data recursively
    cleaned_data = remove_keys_recursive(json_data, KEYS_TO_REMOVE)

    print("Data cleaned.")

    # 3. Write the cleaned data to a new JSON file
    with open(OUTPUT_FILE, "w") as f:
        # Use an indent for a nicely formatted output
        json.dump(cleaned_data, f, indent=4)

    print(f"Cleaned data saved to {OUTPUT_FILE}")

except FileNotFoundError:
    print(f"Error: The file '{INPUT_FILE}' was not found.")
except json.JSONDecodeError:
    print(f"Error: Failed to decode JSON from '{INPUT_FILE}'. Check the file format.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
