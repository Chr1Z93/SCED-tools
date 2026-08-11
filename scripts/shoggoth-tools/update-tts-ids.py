import json
import os
from pathlib import Path

english_folder = Path(
    r"C:\git\SCED-downloads\decomposed\campaign\Alice in Wonderland\AliceinWonderland.39916d"
)
german_folder = Path(
    r"C:\git\SCED-downloads\decomposed\language-pack\German - Fan Campaigns\German-FanCampaigns.GermanFC\AliceinWonderland.209aaa"
)
name_map_path = Path("alice_mapping.json")


def get_metadata_obj(file_path, data):
    base_name = os.path.splitext(file_path)[0]
    gmnotes_file = base_name + ".gmnotes"

    if os.path.exists(gmnotes_file):
        with open(gmnotes_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    try:
        return json.loads(data.get("GMNotes", ""))
    except (json.JSONDecodeError, TypeError):
        return {}


def update_tts_ids():
    # load existing map of english name -> german name
    with open(name_map_path, "r", encoding="utf-8") as f:
        english_to_german_name = json.load(f)

    # create a map of german name -> ID
    english_name_to_id = {}
    for root, dirs, files in os.walk(english_folder):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            metadata = get_metadata_obj(file_path, data)
            name = data["Nickname"]

            if name not in english_to_german_name:
                print(f"No translation found for {name}")
                continue

            german_name = english_to_german_name[name]
            id = metadata.get("id", metadata.get("TtsZoopGuid"))

            if not id:
                print(f"No ID found for {name}")
                continue

            english_name_to_id[german_name] = id

    # loop through german cards, updating every ID based on the two maps
    # 1: german name -> english name | 2: english name -> ID
    # if no match found, change ID to "NOT-FOUND"
    # if multiple cards with the same name BUT different original ID are found, change ID to "CONFLICT" (for all cards with that name)


if __name__ == "__main__":
    update_tts_ids()
