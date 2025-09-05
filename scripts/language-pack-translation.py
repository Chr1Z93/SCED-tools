# This adds 500 to the ArkhamDB IDs for a localized project (that stores IDs in Nicknames)

import json
import os
import requests

# CONFIGURATION
LOCALE = "DE"
INPUT_FILE = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German - Campaigns\LanguagePackGerman-Campaigns.GermanC\DieScharlachrotenSchlssel.72223c.json"

# Globals / Derived data
input_folder_path = os.path.splitext(INPUT_FILE)[0]
arkhambuild_url = f"https://api.arkham.build/v1/cache/cards/{LOCALE.lower()}"
renaming_cache = {}
skipped_files = []


def load_translation_data():
    global translation_data
    translation_data = {}

    try:
        response = requests.get(arkhambuild_url)
        response.raise_for_status()

        # Create a lookup map
        for item in response.json()["data"]["all_card"]:
            key = item["id"]

            # Special handling for cards with type "Key" (double-sided)
            if item["type_code"] == "key":
                # Remove the "a"/"b" from the key
                key = item["id"][:-1]

            # Metadata correction
            if key == "09569b":
                continue

            translation_data[key] = item

    except requests.exceptions.HTTPError as e:
        print(f"Couldn't get translation data (HTTP {e.response.status_code})")
    except requests.exceptions.ConnectionError as e:
        print(f"Couldn't get translation data (Connection Error: {e})")
    except json.JSONDecodeError:
        print(f"Couldn't parse API response")


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
            else:
                updated_list.append(item)

        data["ContainedObjects_order"] = updated_list

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

        if adb_id in translation_data:
            translation = translation_data[adb_id]
        else:
            skipped_files.append(adb_id)
            continue

        if "name" in translation:
            translated_name = translation["name"]
        elif "real_name" in translation:
            translated_name = translation["real_name"]
        else:
            skipped_files.append(adb_id)
            continue

        data["Nickname"] = translated_name
        data["Description"] = translation.get("subname", "")
        data["GMNotes"] = '{\n  "id": "' + adb_id + '"\n}'

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # Rename the file after updating its content
        clean_name = remove_characters(translated_name)
        new_filename = clean_name + "." + data["GUID"] + ".json"
        new_file_path = os.path.join(folder_path, new_filename)

        # Cache renaming, slicing to remove ".json"
        renaming_cache[filename[:-5]] = new_filename[:-5]

        os.rename(file_path, new_file_path)
        print(f"Processed file: {filename} -> {new_filename}")


def remove_characters(text):
    # return re.sub(r"[^a-zA-Z0-9-]", "", text)
    chars_to_remove = [" ", ".", "(", ")", "?", '"']
    for char in chars_to_remove:
        text = text.replace(char, "")
    return text


def main():
    load_translation_data()
    update_json_files_in_folder(input_folder_path)
    update_json_data(INPUT_FILE)

    for item in skipped_files:
        print(f"Skipped {item}")


if __name__ == "__main__":
    main()
