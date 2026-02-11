# This fixes mismatches in CardID and custom deck data
# WARNING: Not built for cards in decks

import json
import os

# CONFIGURATION
INPUT_FOLDER = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack Spanish - Player Cards\LanguagePackSpanish-PlayerCards.SpanishI"


def update_json_files_in_folder(folder_path):
    """Updates the 'CardID' field."""

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

            card_id = data["CardID"]
            deck_id = list(data["CustomDeck"].keys())[0]
            proper_card_id = int(deck_id + str(card_id)[-2:])

            if card_id == proper_card_id:
                continue

            data["CardID"] = proper_card_id

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

            print(f"Processed file: {filename}")


if __name__ == "__main__":
    update_json_files_in_folder(INPUT_FOLDER)
