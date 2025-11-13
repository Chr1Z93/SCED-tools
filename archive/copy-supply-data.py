# Copies the gm notes for supply cards from one folder to another

import os
import json

# Set the root directory where your JSON files are located.
SOURCE_DIRECTORY = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Russian - Campaigns\LanguagePackRussian-Campaigns.RussianC"
TARGET_DIRECTORY = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Korean - Campaigns\LanguagePackKorean-Campaigns.KoreanC"

# Decksheet of the target deck
TARGET_URL = "https://steamusercontent-a.akamaihd.net/ugc/2260310642906139666/1DF80FB7CC3593AD21F04F1CC3512EF00555BF7B/"


card_id_to_gm_notes_map = {}


def read_files_in_directory(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.loads(f.read())

                if "CardID" not in data or "GMNotes" not in data:
                    continue

                # STEP 1: Decode the GMNotes string into a Python dict
                md = json.loads(data["GMNotes"])
                
                # STEP 2: Now check the 'id' field of the inner dictionary
                if md.get("id", "").startswith("ES04"):
                    card_id = data["CardID"] % 100
                    card_id_to_gm_notes_map[card_id] = data["GMNotes"]

    print("\n--- ✨ Reading Complete! ---")


def process_files_in_directory(directory):
    for root, _, files in os.walk(directory):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            # Read the original file to load JSON data
            # Using utf-8-sig to handle potential BOM (Byte Order Mark)
            with open(file_path, "r", encoding="utf-8-sig") as f:
                content = f.read()

                if TARGET_URL not in content:
                    continue

                data = json.loads(content)

                if "CardID" not in data or "GMNotes" in data:
                    continue

                card_id = data["CardID"] % 100

                if card_id not in card_id_to_gm_notes_map:
                    continue

                data["GMNotes"] = card_id_to_gm_notes_map[card_id]

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    separators=(",", ": "),
                    ensure_ascii=False,
                )
                f.write("\n")

    print("\n--- ✨ Copying Complete! ---")


if __name__ == "__main__":
    read_files_in_directory(SOURCE_DIRECTORY)
    process_files_in_directory(TARGET_DIRECTORY)
