import os
import json
import shutil
import pandas as pd

TABLE_PATH = r"C:\Users\pulsc\Downloads\TRans(KR).csv"
SOURCE_FOLDER = r"C:\git\SCED-downloads\decomposed\campaign\The Scarlet Keys"
TARGET_FOLDER = r"C:\git\SCED-downloads\decomposed\language-pack\Korean - Campaigns\Korean-Campaigns.KoreanC\TheScarletKeys.020bf5"


def process_card_jsons(table_path, source_dir, target_dir):
    # Load the URL mapping
    df = pd.read_csv(table_path, sep=';')
    url_map = dict(zip(df["old_url"], df["new_url"]))

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # os.walk traverses the directory tree (root, subdirs, files)
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            if filename.endswith(".json"):
                # Construct full path to the source file
                file_path = os.path.join(root, filename)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    name_value = data.get("Name")
                    if name_value == "Card" or name_value == "CardCustom":
                        found_match = False
                        json_str = json.dumps(data, ensure_ascii=False)

                        for old_url, new_url in url_map.items():
                            if old_url in json_str:
                                json_str = json_str.replace(old_url, new_url)
                                found_match = True

                        if found_match:
                            # Because we are flattening subfolders, we check if the file
                            # already exists in the target to avoid overwriting blindly
                            target_path = os.path.join(target_dir, filename)
                            updated_data = json.loads(json_str)

                            with open(target_path, "w", encoding="utf-8") as f:
                                json.dump(updated_data, f, indent=4, ensure_ascii=False)

                            # Check for matching .gmnotes file
                            # We replace the extension and check if that file exists in the same source folder
                            gmnotes_filename = filename.replace(".json", ".gmnotes")
                            gmnotes_source_path = os.path.join(root, gmnotes_filename)
                            
                            if os.path.exists(gmnotes_source_path):
                                target_gmnotes_path = os.path.join(target_dir, gmnotes_filename)
                                shutil.copy2(gmnotes_source_path, target_gmnotes_path)
                                print(f"Processed: {filename} (+ .gmnotes copied)")
                            else:
                                print(f"Processed: {filename} (No .gmnotes found)")

                except (json.JSONDecodeError, IOError) as e:
                    print(f"Skipping {filename} due to error: {e}")


if __name__ == "__main__":
    process_card_jsons(TABLE_PATH, SOURCE_FOLDER, TARGET_FOLDER)
