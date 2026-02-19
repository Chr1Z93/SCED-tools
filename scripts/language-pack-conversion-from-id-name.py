# This converts a localized project with IDs as names to properly named cards

import json
import os
import requests

# CONFIGURATION
LOCALE = "ES"

# This path can be a single .json file or a root folder containing many subfolders
INPUT_PATH = r"C:\git\SCED-downloads\decomposed\language-pack\Spanish - Campaigns\Spanish-Campaigns.SpanishC"

# These cards are either double-sided and we only want the front-data
# or they are for some other reason weirdly indexed in the data.
REMOVE_SUFFIX = [
    "09600",
    "09606",
    "09607",
    "09615",
    "09653",
    "09654",
    "09655",
    "09674",
    "09675",
    "09676",
    "09679",
    "09747",
    "09748",
    "09749",
]

# Globals / Derived data
arkhambuild_url = f"https://api.arkham.build/v1/cache/cards/{LOCALE.lower()}"
renaming_cache = {}
skipped_files = []
translation_data = {}


def load_translation_data():
    global translation_data
    try:
        response = requests.get(arkhambuild_url)
        response.raise_for_status()

        # Create a lookup map
        for item in response.json()["data"]["all_card"]:
            key = item["id"]

            # Special handling for cards with type "Key" and double-sided cards
            if item["type_code"] == "key" or item["id"][:-1] in REMOVE_SUFFIX:
                # Remove the "a"/"b" from the key
                key = item["id"][:-1]

                # If base version is already in the data, skip this
                if key in translation_data and item["id"][-1] == "b":
                    continue

            # Metadata correction
            if key == "09569b":
                continue

            translation_data[key] = item

    except Exception as e:
        print(f"Error fetching translation data: {e}")


def remove_characters(text):
    chars_to_remove = [" ", ".", "(", ")", "?", '"', "“", "„", "”"]
    for char in chars_to_remove:
        text = text.replace(char, "")
    return text


def is_already_processed(data):
    """Checks if the GMNotes already contains the correct ID."""
    gm_notes_raw = data.get("GMNotes", "")
    if not gm_notes_raw:
        return False
    try:
        # Try to parse the GMNotes string as JSON
        notes_json = json.loads(gm_notes_raw)
        return "id" in notes_json
    except json.JSONDecodeError:
        return False


def process_files_recursively(base_path):
    """
    Step 1: Recursively rename files and update their internal ID metadata.
    Fills the renaming_cache for Step 2.
    """
    global renaming_cache

    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue

            # skip already processed files
            if is_already_processed(data):
                continue

            # Check if Nickname exists and is in our translation map
            adb_id = data.get("Nickname")
            if not adb_id:
                continue

            if adb_id not in translation_data:
                # We skip files that don't have a valid ID in the Nickname field
                skipped_files.append(adb_id)
                continue

            translation = translation_data[adb_id]
            translated_name = translation.get("name") or translation.get("real_name")

            if not translated_name:
                skipped_files.append(adb_id)
                continue

            # Update Metadata
            data["Nickname"] = translated_name
            subname = translation.get("subname", "").strip()

            if subname:
                data["Description"] = subname
            else:
                # Remove the key entirely if subname is empty/missing
                data.pop("Description", None)

            data["GMNotes"] = f'{{\n  "id": "{adb_id}"\n}}'

            # Save updated content
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            # Calculate new filename
            clean_name = remove_characters(translated_name)
            guid = data.get("GUID", "NOGUID")
            new_filename = f"{clean_name}.{guid}.json"
            new_file_path = os.path.join(root, new_filename)

            # Store in cache for Step 2 (ContainedObjects_order)
            # We use filename[:-5] to strip '.json'
            renaming_cache[filename[:-5]] = new_filename[:-5]

            # Rename on disk
            try:
                os.rename(file_path, new_file_path)
                print(f"Processed: {filename} -> {new_filename}")
            except OSError as e:
                print(f"Error renaming {filename}: {e}")


def update_contained_objects(base_path):
    """
    Step 2: Recursively update the 'ContainedObjects_order' list in all JSONs
    using the renaming_cache created in Step 1.
    """
    for root, dirs, files in os.walk(base_path):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue

            if "ContainedObjects_order" in data and isinstance(
                data["ContainedObjects_order"], list
            ):
                updated_list = []
                changed = False
                for item in data["ContainedObjects_order"]:
                    if item in renaming_cache:
                        updated_list.append(renaming_cache[item])
                        changed = True
                    else:
                        updated_list.append(item)

                if changed:
                    data["ContainedObjects_order"] = updated_list
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                        f.write("\n")
                    print(f"Updated object order in: {filename}")


def main():
    load_translation_data()

    if not os.path.exists(INPUT_PATH):
        print(f"Path not found: {INPUT_PATH}")
        return

    # If it's a file, we usually want to process the folder it's in
    target_path = INPUT_PATH
    if os.path.isfile(INPUT_PATH):
        target_path = os.path.dirname(INPUT_PATH)

    print("--- Step 1: Renaming and Metadata ---")
    process_files_recursively(target_path)

    print("\n--- Step 2: Updating Contained Objects Order ---")
    update_contained_objects(target_path)

    if skipped_files:
        print("\n--- Skipped IDs ---")
        for item in sorted(set(skipped_files)):
            print(item)


if __name__ == "__main__":
    main()
