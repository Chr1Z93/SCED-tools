# This adds 500 to the ArkhamDB IDs for a localized project (that stores IDs in Nicknames)

import json
import os
import re
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

# CONFIGURATION
LOCALE = "DE"
INPUT_FILE = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German - Campaigns\LanguagePackGerman-Campaigns.GermanC\AmRandederWelt.f4f47a.json"

# Derived data
input_folder_path = os.path.splitext(INPUT_FILE)[0]
script_dir = os.path.dirname(__file__)
translation_cache_file_name = f"translation_cache_{LOCALE.lower()}.json"
translation_cache_file = os.path.join(script_dir, translation_cache_file_name)
arkhamdb_url = f"https://{LOCALE.lower()}.arkhamdb.com/api/public/card/"
renaming_cache = {}


def load_translation_cache():
    global translation_cache
    if os.path.exists(translation_cache_file):
        with open(translation_cache_file, "r", encoding="utf-8") as file:
            translation_cache = json.load(file)
    else:
        translation_cache = {}


def save_translation_cache():
    with open(translation_cache_file, "w", encoding="utf-8") as f:
        json.dump(translation_cache, f, ensure_ascii=False, indent=2)


def get_translated_name(adb_id):
    """Get the translated card name from cache / ArkhamDB"""
    global translation_cache

    if adb_id in translation_cache:
        return translation_cache[adb_id]

    try:
        response = urlopen(arkhamdb_url + adb_id)
    except HTTPError as e:
        print(f"{adb_id} - couldn't get translated name (HTTP {e.code})")
    except URLError as e:
        print(f"{adb_id} - couldn't get translated name (URL {e.reason})")

    try:
        data_json = json.loads(response.read())
    except json.JSONDecodeError:
        print(f"{adb_id} - couldn't parse JSON")

    try:
        translation = {"name": data_json["name"], "subname": data_json.get("subname")}
        translation_cache[adb_id] = translation
        return translation
    except KeyError:
        print(f"{adb_id} - JSON response did not contain 'name' key")


def update_json_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "ContainedObjects_order" in data and isinstance(
        data["ContainedObjects_order"], list
    ):
        updated_list = []
        for item in data["ContainedObjects_order"]:
            if item in renaming_cache:
                updated_item = renaming_cache[item]
                updated_list.append(updated_item)

        data["ContainedObjects_order"] = updated_list
        print(f"Updated 'ContainedObjects_order' in: {file_path}")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")


def update_json_files_in_folder(folder_path):
    """Renames the files and updates the 'Nickname' / 'Description' fields."""
    global renaming_cache

    if not os.path.isdir(folder_path):
        print(f"Error: The directory {folder_path} was not found.")
        return

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        adb_id = data["Nickname"]
        translation = get_translated_name(adb_id)
        if translation:
            data["Nickname"] = translation["name"]
            data["Description"] = translation.get("subname", "")
            data["GMNotes"] = '{\n  "id": "' + adb_id + '"\n}'

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            # Rename the file after updating its content
            clean_name = remove_characters(translation["name"])
            new_filename = clean_name + "." + data["GUID"] + ".json"
            new_file_path = os.path.join(folder_path, new_filename)

            # Cache renaming, slicing to remove ".json"
            renaming_cache[filename[:-5]] = new_filename[:-5]

            os.rename(file_path, new_file_path)
            print(f"Processed file: {filename} -> {new_filename}")


def remove_characters(text):
    # return re.sub(r"[^a-zA-Z0-9-]", "", text)
    return text.replace(" ", "").replace(".", "").replace("(", "").replace(")", "")


def main():
    load_translation_cache()
    update_json_files_in_folder(input_folder_path)
    update_json_data(INPUT_FILE)
    save_translation_cache()


if __name__ == "__main__":
    main()
