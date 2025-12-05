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
            name_with_guid = initial_name + "." + new_guid
            new_gmnotes_path = os.path.join(root, name_with_guid + ".gmnotes")
            old_json_path = os.path.join(root, old_name_with_guid + ".json")
            new_json_path = os.path.join(root, name_with_guid + ".json")

            # remove the "alternate_ids" field from the .gmnotes file
            del metadata["alternate_ids"]

            # update existing .gmnotes file
            if metadata["cycle"] == "Core":
                metadata["cycle"] = "Core Set"
            with open(old_gmnotes_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                f.write("\n")
    
            # save the .gmnotes file with the new GUID
            metadata["id"] = alt_id
            metadata["cycle"] = "Revised Core Set"
            with open(new_gmnotes_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                f.write("\n")
            
            # load the .json file with the same name 
            with open(old_json_path, "r", encoding="utf-8") as f:
                jsondata = json.load(f)

            jsondata["GUID"] = new_guid
            jsondata["CardID"] = 100
            jsondata["GMNotes_path"] = replace_guid(jsondata["GMNotes_path"], new_guid)
            jsondata["CustomDeck"] = {
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
                json.dump(jsondata, f, indent=2, ensure_ascii=False)
                f.write("\n")

                
def replace_guid(original_string, new_guid):
    # The pattern looks for:
    # 1. A literal dot: '\.'
    # 2. Six hexadecimal characters (0-9, a-f, A-F): '[0-9a-fA-F]{6}'
    # 3. A lookahead ensuring the GUID is followed by either a dot or the end of the string: '(?=\.|\/|$)'
    pattern = r'\.([0-9a-fA-F]{6})(?=\.|\/|$)'
    return re.sub(pattern, f".{new_guid}", original_string, count=1)

if __name__ == "__main__":
    split_revised_cards(TARGET_DIRECTORY)
