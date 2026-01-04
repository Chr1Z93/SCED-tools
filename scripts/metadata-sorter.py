# Sorts the metadata based on the specified order

import json
import os

BASE_DIR = r"C:\git\SCED-downloads\decomposed"

# Define the order of keys for top-level structure
KEY_ORDER = [
    "id",
    "alternate_ids",
    "type",
    "slot",
    "class",
    "cost",
    "level",
    "traits",
    "specialist",
    "startsInHand",
    "startsInPlay",
    "permanent",
    "weakness",
    "basicWeaknessCount",
    "classRestriction",
    "modeRestriction",
    "hidden",
    "willpowerIcons",
    "intellectIcons",
    "combatIcons",
    "agilityIcons",
    "wildIcons",
    "dynamicIcons",
    "negativeIcons",
    "elderSignEffect",
    "health",
    "sanity",
    "bonded",
    "uses",
    "victory",
    "doomThreshold",
    "customizations",
    "cycle",
    "extraToken",
    "starterDeck",
    "signatures",
    "locationFront",
    "locationBack",
    "TtsZoopGuid",
]

# Define the order of keys specifically for subtables (nested dictionaries)
SUBTABLE_KEY_ORDER = [
    "victory",
    "vengeance",
    "icons",
    "connections",
    "uses",
    "count",
    "countPerInvestigator",
    "maxCount",
    "id",
    "replenish",
    "type",
    "token",
    "name",
    "xp",
    "text",
    "front",
    "back",
    "Skull",
    "Cultist",
    "Tablet",
    "Elder Thing",
    "description",
    "modifier",
]


def sortJSONKeys(data, is_top_level=True):
    try:
        if isinstance(data, dict):
            sorted_dict = {}

            if is_top_level:
                # For the top-level dictionary, apply the specified key order
                for key in KEY_ORDER:
                    if key in data:
                        sorted_dict[key] = sortJSONKeys(data[key], is_top_level=False)
                # Add any remaining keys in alphabetical order
                for key in sorted(data.keys()):
                    if key not in sorted_dict:
                        sorted_dict[key] = sortJSONKeys(data[key], is_top_level=False)
            else:
                # For subtables, apply SUBTABLE_KEY_ORDER first, then alphabetically sort the remaining keys
                for key in SUBTABLE_KEY_ORDER:
                    if key in data:
                        sorted_dict[key] = sortJSONKeys(data[key], is_top_level=False)
                for key in sorted(data.keys()):
                    if key not in sorted_dict:
                        sorted_dict[key] = sortJSONKeys(data[key], is_top_level=False)

            return sorted_dict

        elif isinstance(data, list):
            # Recursively sort any dictionaries in the list
            return [sortJSONKeys(item, is_top_level=False) for item in data]

        else:
            # Return non-dict and non-list items as is
            return data

    except Exception as e:
        print(f"Error sorting JSON keys: {e}")
        return data  # Return the original data if there's an error


def process_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: File '{file_path}' contains invalid JSON.")
        return
    except UnicodeDecodeError as e:
        print(f"Error: Could not decode file '{file_path}'. {e}")
        return
    except IOError as e:
        print(f"Error: Could not read file '{file_path}'. {e}")
        return

    try:
        modified_data = sortJSONKeys(data)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(modified_data, f, indent=2)
            f.write("\n")  # Add an empty line at the end of the file
    except IOError as e:
        print(f"Error: Could not write to file '{file_path}'. {e}")
    except Exception as e:
        print(f"Unexpected error processing file '{file_path}': {e}")


def main():
    if not os.path.exists(BASE_DIR):
        print(f"Error: Directory '{BASE_DIR}' does not exist.")
        return

    for path, _, files in os.walk(BASE_DIR):
        for file in files:
            file_path = os.path.join(path, file)
            if file.endswith(".gmnotes"):
                process_file(file_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
