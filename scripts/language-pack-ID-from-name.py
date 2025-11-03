# This converts a localized project with names cards to GMNotes with IDs

import json
import os
import requests

# CONFIGURATION
LOCALE = "ES"
INPUT_FOLDER = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Spanish - Player Cards\LanguagePackSpanish-PlayerCards.SpanishI"

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
skipped_files = []


def load_translation_data():
    global translation_data
    translation_data = {}

    try:
        response = requests.get(arkhambuild_url)
        response.raise_for_status()

        # Create a lookup map
        for item in response.json()["data"]["all_card"]:
            if "name" in item:
                key = item["name"]
            else:
                print(f"{item["code"]} does not have a name.")
                continue

            # Append (XP)
            if "xp" in item and isinstance(item["xp"], int) and item["xp"] > 0:
                key += " (" + str(item["xp"]) + ")"

            translation_data[key] = item

    except requests.exceptions.HTTPError as e:
        print(f"Couldn't get translation data (HTTP {e.response.status_code})")
    except requests.exceptions.ConnectionError as e:
        print(f"Couldn't get translation data (Connection Error: {e})")
    except json.JSONDecodeError:
        print(f"Couldn't parse API response")


def update_json_files_in_folder(folder_path):
    """Updates the 'GMNotes' field."""

    if not os.path.isdir(folder_path):
        print(f"Error: The directory {folder_path} was not found.")
        return

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "GMNotes" in data:
            continue

        nickname = data["Nickname"]

        if nickname in translation_data:
            translation = translation_data[nickname]
        else:
            skipped_files.append(nickname)
            continue

        if "code" in translation:
            adb_id = translation["code"]
        else:
            skipped_files.append(nickname)
            continue

        # maybe update description with subtitle
        if "Description" not in data and "subname" in translation:
            data["Description"] = translation["subname"]
        data["GMNotes"] = '{"id": "' + adb_id + '"}'

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

        print(f"Processed file: {filename} ({adb_id})")


def remove_characters(text):
    # return re.sub(r"[^a-zA-Z0-9-]", "", text)
    chars_to_remove = [" ", ".", "(", ")", "?", '"', "“", "„", "”"]
    for char in chars_to_remove:
        text = text.replace(char, "")
    return text


def main():
    load_translation_data()
    update_json_files_in_folder(INPUT_FOLDER)

    for item in skipped_files:
        print(f"Skipped {item}")


if __name__ == "__main__":
    main()
