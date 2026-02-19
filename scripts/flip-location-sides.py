# This flips the FaceURL and BackURL for locations

import json
import os
import requests

# CONFIGURATION
INPUT_FOLDER = r"C:\git\SCED-downloads\decomposed\language-pack\Polish - Campaigns\Polish-Campaigns.PolishC\NightoftheZealot.5b3bc8"

# Globals / Derived data
arkhambuild_url = f"https://api.arkham.build/v1/cache/cards/"
skipped_files = []


def load_translation_data():
    global translation_data
    translation_data = {}

    try:
        response = requests.get(arkhambuild_url)
        response.raise_for_status()

        # Create a lookup map
        for item in response.json()["data"]["all_card"]:
            if "type_code" not in item or "double_sided" not in item:
                continue

            if item["type_code"] != "location" or item["double_sided"] != True:
                continue

            translation_data[item["code"]] = True

    except requests.exceptions.HTTPError as e:
        print(f"Couldn't get translation data (HTTP {e.response.status_code})")
    except requests.exceptions.ConnectionError as e:
        print(f"Couldn't get translation data (Connection Error: {e})")
    except json.JSONDecodeError:
        print(f"Couldn't parse API response")


def update_json_files_in_folder(folder_path):
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

            # Skip cards without GMNotes
            if "GMNotes" not in data:
                continue

            try:
                md = json.loads(data["GMNotes"])
                if "id" not in md:
                    continue

                adb_id = md["id"]

                if adb_id not in translation_data:
                    skipped_files.append(adb_id)
                    continue

                # Skip non-locations
                if translation_data[adb_id] == False:
                    continue

                # Flip URLs
                custom_deck = data["CustomDeck"]
                deck_id = list(data["CustomDeck"].keys())[0]
                card_details = custom_deck[deck_id]
                current_face_url = card_details["FaceURL"]
                current_back_url = card_details["BackURL"]
                card_details["FaceURL"] = current_back_url
                card_details["BackURL"] = current_face_url

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")

                print(f"Processed file: {filename} ({adb_id})")
            
            except json.JSONDecodeError:
                continue


def main():
    load_translation_data()
    update_json_files_in_folder(INPUT_FOLDER)

    for item in skipped_files:
        print(f"Skipped {item}")


if __name__ == "__main__":
    main()
