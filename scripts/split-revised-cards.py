# Splits the revised core set cards into separate files
import json
import os
import re

# --- Configuration ---
TARGET_DIRECTORY = r"C:\git\SCED\objects\AllPlayerCards.15bb07"

def split_revised_cards(base_folder):
    for root, _, files in os.walk(base_folder):
        for file_name in files:
            if not file_name.endswith((".gmnotes")):
                continue

            old_gmnotes_path = os.path.join(root, file_name)

            # load .gmnotes file
            with open(old_gmnotes_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # skip already split cards
            if "alternate_ids" not in metadata:
                continue
            
            alt_id = None
            for id in metadata["alternate_ids"]:
                num = 0
                if "a" in id or "b" in id or "c" in id or "d" in id:
                    num = int(id[:-1])
                elif "-" in id:
                    num = int(id.split("-")[0])
                else:
                    num = int(id)

                # make sure this is from the revised core set
                if num > 1500 and num < 2000:
                    alt_id = id
                    break

            if alt_id == None:
                continue

            # name without file extension
            old_name_with_guid = os.path.splitext(file_name)[0]
            new_guid = "rev" + alt_id

            # build the paths
            initial_name = old_name_with_guid.split(".")[0]
            new_name_with_guid = initial_name + "." + new_guid
            new_gmnotes_path = os.path.join(root, new_name_with_guid + ".gmnotes")
            old_json_path = os.path.join(root, old_name_with_guid + ".json")
            new_json_path = os.path.join(root, new_name_with_guid + ".json")

            # remove the "alternate_ids" field from the .gmnotes file
            del metadata["alternate_ids"]

            # update existing .gmnotes file
            if "cycle" not in metadata:
                print(f"No cycle in {file_name}")
                metadata["cycle"] = "Core"
            with open(old_gmnotes_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                f.write("\n")
    
            # save the .gmnotes file with the new GUID
            metadata["id"] = alt_id
            metadata["cycle"] = "Revised Core"
            with open(new_gmnotes_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                f.write("\n")
            
            # load the .json file with the same name 
            with open(old_json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            json_data["GUID"] = new_guid
            json_data["CardID"] = 100
            json_data["GMNotes_path"] = replace_last_guid(json_data["GMNotes_path"], new_guid)
            json_data["CustomDeck"] = {
                "1": {
                    "BackIsHidden": True,
                    "BackURL": "",
                    "FaceURL": "",
                    "NumHeight": 1,
                    "NumWidth": 1,
                    "Type": 0,
                    "UniqueBack": True
                }
            }

            # save the .json file with the new GUID
            with open(new_json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                f.write("\n")

                
def replace_last_guid(original_string, new_guid):
    # Looks for a dot, followed by 6 hex chars, followed by a dot, slash, or end-of-string.
    pattern = r'\.([0-9a-fA-F]{6})(?=\.|\/|$)'
    
    # 1. Find ALL matches in the string
    matches = list(re.finditer(pattern, original_string))
    
    # 2. Check if any matches were found
    if not matches:
        return original_string # Return the original string if no GUIDs were found

    # 3. Get the last match object
    last_match = matches[-1]
    
    # Get the start and end index of the portion we want to replace (the dot and the GUID)
    start_index = last_match.start()
    end_index = last_match.end()
    
    # 4. Construct the new string using slicing and the replacement value
    # String = (Part before the match) + (New GUID with leading dot) + (Part after the match)
    new_string = (
        original_string[:start_index] + 
        f".{new_guid}" + 
        original_string[end_index:]
    )
    
    return new_string

if __name__ == "__main__":
    split_revised_cards(TARGET_DIRECTORY)
