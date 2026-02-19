# This converts a localized project with named cards to GMNotes with IDs

import json
import os
import requests

# CONFIGURATION
LOCALE = "ES"
TABOO_SUFFIX = " (Tabú)"
INPUT_FOLDER = r"C:\git\SCED-downloads\decomposed\language-pack\Spanish - Campaigns\Spanish-Campaigns.SpanishC"

# Globals / Derived data
UPGRADESHEET_URL = "https://steamusercontent-a.akamaihd.net/ugc/1814412497119682452/BD224FCE1980DBA38E5A687FABFD146AA1A30D0E/"
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
                # print(f"{item["code"]} does not have a name.")
                continue

            # Append (XP)
            if "xp" in item and isinstance(item["xp"], int) and item["xp"] > 0:
                key += " (" + str(item["xp"]) + ")"

            # Use lower string for lookup
            key = key.lower()

            # If this already exists, keep the lower number
            if key in translation_data:
                if int(translation_data[key]["code"][:5]) < int(item["code"][:5]):
                    continue

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

    for root, dirs, files in os.walk(folder_path):
        if ".git" in dirs:
            dirs.remove(".git")

        if ".github" in dirs:
            dirs.remove(".github")

        if ".vscode" in dirs:
            dirs.remove(".vscode")

        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Only process cards
            if data["Name"] != "Card" and data["Name"] != "CardCustom":
                continue

            # Skip cards with GMNotes
            if "GMNotes" in data:
                continue

            nickname = data["Nickname"]

            is_taboo = False
            is_upgradesheet = False

            # Handle taboo cards
            if nickname.endswith(TABOO_SUFFIX):
                # Remove the suffix by slicing
                nickname = nickname[: -len(TABOO_SUFFIX)]
                is_taboo = True

            # Attempt to find the ID based on nickname
            if nickname.lower() in translation_data:
                translation = translation_data[nickname.lower()]
            else:
                skipped_files.append(nickname)
                continue

            if "code" in translation:
                adb_id = translation["code"]

                # Append "-t" for taboo cards
                if is_taboo:
                    adb_id += "-t"

                # Append "-c" for UpgradeSheets
                if "customization_options" in translation:
                    # Check for the URL
                    custom_deck = data["CustomDeck"]
                    deck_info = list(custom_deck.values())[0]
                    if deck_info["BackURL"] == UPGRADESHEET_URL:
                        is_upgradesheet = True
                        adb_id += "-c"
            else:
                skipped_files.append(nickname)
                continue

            # Maybe update description with subtitle
            if "subname" in translation and not is_upgradesheet:
                data["Description"] = translation["subname"]
            data["GMNotes"] = '{"id": "' + adb_id + '"}'

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            print(f"Processed file: {filename} ({adb_id})")


def remove_characters(text):
    # Return re.sub(r"[^a-zA-Z0-9-]", "", text)
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
