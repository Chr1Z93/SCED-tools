# Splits the revised core set cards into separate files
import json
import os
import re

# --- Configuration ---
TARGET_DIRECTORY = r"C:\git\SCED\objects\AllPlayerCards.15bb07"


def split_revised_cards(base_folder):
    created_count = 0  # initialize counter

    for root, _, files in os.walk(base_folder):
        for file_name in files:
            if not file_name.endswith(".gmnotes"):
                continue

            old_gmnotes_path = os.path.join(root, file_name)

            # load .gmnotes file
            with open(old_gmnotes_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # skip already split cards
            if "alternate_ids" not in metadata:
                continue

            # skip investigators / minicards
            if metadata.get("type") in ["Investigator", "Minicard"]:
                continue

            # Identify the Revised Core ID
            rev_id = None
            remaining_ids = []

            for alt_id in metadata["alternate_ids"]:
                # Logic to extract the numeric part
                if any(char in alt_id for char in "abcd"):
                    num = int(alt_id[:-1])
                elif "-" in alt_id:
                    num = int(alt_id.split("-")[0])
                else:
                    num = int(alt_id)

                # Check if it belongs to Revised Core (1501-1999)
                if 1500 < num < 2000:
                    rev_id = alt_id
                else:
                    remaining_ids.append(alt_id)

            # If no Revised ID found, we don't need to split this file
            if rev_id is None:
                continue

            # Update the original file's alternate_ids
            if remaining_ids:
                metadata["alternate_ids"] = remaining_ids
            else:
                del metadata["alternate_ids"]

            # Prepare path names
            old_name_with_guid = os.path.splitext(file_name)[0]
            new_guid = "rev" + rev_id
            initial_name = old_name_with_guid.split(".")[0]
            new_name_with_guid = f"{initial_name}.{new_guid}"

            new_gmnotes_path = os.path.join(root, new_name_with_guid + ".gmnotes")
            old_json_path = os.path.join(root, old_name_with_guid + ".json")
            new_json_path = os.path.join(root, new_name_with_guid + ".json")

            # Update and save existing (Original) .gmnotes file
            if "cycle" not in metadata:
                print(f"{old_gmnotes_path}: No cycle")
                metadata["cycle"] = "Core"
            with open(old_gmnotes_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                f.write("\n")

            # Prepare and save NEW .gmnotes file (Revised)
            # We create a deep copy or temporary dict so we don't include
            # the 'remaining_ids' in the Revised file
            revised_metadata = metadata.copy()
            if "alternate_ids" in revised_metadata:
                del revised_metadata["alternate_ids"]

            revised_metadata["id"] = rev_id
            revised_metadata["cycle"] = "Revised Core"

            with open(new_gmnotes_path, "w", encoding="utf-8") as f:
                json.dump(revised_metadata, f, indent=2, ensure_ascii=False)
                f.write("\n")

            # Load and update the .json file
            with open(old_json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            json_data["GUID"] = new_guid
            json_data["CardID"] = 100
            json_data["GMNotes_path"] = replace_last_guid(
                json_data["GMNotes_path"], new_guid
            )
            json_data["CustomDeck"] = {
                "1": {
                    "BackIsHidden": True,
                    "BackURL": "https://steamusercontent-a.akamaihd.net/ugc/2342503777940352139/A2D42E7E5C43D045D72CE5CFC907E4F886C8C690/",
                    "FaceURL": f"{rev_id}.jpg",
                    "NumHeight": 1,
                    "NumWidth": 1,
                    "Type": 0,
                    "UniqueBack": True,
                }
            }

            # Save the .json file with the new GUID
            with open(new_json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            # Increment counter
            created_count += 1

    print("---")
    print(f"Process complete. Total new card objects created: {created_count}")


def replace_last_guid(original_string, new_guid):
    # Looks for a dot, followed by 6 hex chars, followed by a dot, slash, or end-of-string.
    pattern = r"\.([0-9a-fA-F]{6})(?=\.|\/|$)"

    # 1. Find ALL matches in the string
    matches = list(re.finditer(pattern, original_string))

    # 2. Check if any matches were found
    if not matches:
        return original_string  # Return the original string if no GUIDs were found

    # 3. Get the last match object
    last_match = matches[-1]

    # Get the start and end index of the portion we want to replace (the dot and the GUID)
    start_index = last_match.start()
    end_index = last_match.end()

    # 4. Construct the new string using slicing and the replacement value
    # String = (Part before the match) + (New GUID with leading dot) + (Part after the match)
    new_string = (
        original_string[:start_index] + f".{new_guid}" + original_string[end_index:]
    )

    return new_string


if __name__ == "__main__":
    split_revised_cards(TARGET_DIRECTORY)
