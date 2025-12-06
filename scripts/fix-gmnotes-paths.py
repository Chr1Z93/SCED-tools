import json
import os
from pathlib import Path

# --- Configuration ---
TARGET_DIRECTORY = r"C:\git\SCED\objects\AllPlayerCards.15bb07"
BASE_FOLDER_NAME = Path(TARGET_DIRECTORY).name

def fix_gmnotes_path(base_folder):
    for root, _, files in os.walk(base_folder):
        for file_name in files:
            if not file_name.endswith((".json")):
                continue

            file_path = os.path.join(root, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "GMNotes_path" not in data:
                continue
        
            # name without file extension
            name_with_guid = os.path.splitext(file_name)[0]

            # repair the GMNNotes_path
            rel_dir = os.path.relpath(root, base_folder)
            new_path_parts = [BASE_FOLDER_NAME]

            # Add the relative subdirectory if it's not the base directory itself (represented by '.')
            if rel_dir != ".":
                # Convert the relative path to use forward slashes for the GMNotes_path format
                new_path_parts.append(rel_dir.replace("\\", "/"))

            # Add the final file name with the new extension
            new_path_parts.append(name_with_guid + ".gmnotes")
            
            # Join all parts using a forward slash to match the target format
            new_path = "/".join(new_path_parts)

            if data["GMNotes_path"] == new_path:
                continue

            data["GMNotes_path"] = new_path

            # save the repaired .json file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

                
if __name__ == "__main__":
    fix_gmnotes_path(TARGET_DIRECTORY)
