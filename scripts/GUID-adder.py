# Adds GUIDs to a JSON object

import json
import random
from pathlib import Path


def generate_unique_hex(existing_guids, length=6):
    while True:
        new_guid = f"{random.getrandbits(length * 4):0{length}x}"
        if new_guid not in existing_guids:
            return new_guid


def replace_empty_guids(obj, existing_guids):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "GUID" and value == "":
                new_guid = generate_unique_hex(existing_guids)
                obj[key] = new_guid
                existing_guids.add(new_guid)
            else:
                replace_empty_guids(value, existing_guids)
    elif isinstance(obj, list):
        for item in obj:
            replace_empty_guids(item, existing_guids)


def process_json_file(filepath):
    path = Path(filepath)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    existing_guids = set()
    replace_empty_guids(data, existing_guids)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
    print(f"Updated GUIDs in {filepath}")


process_json_file(
    r"C:\Users\pulsc\Documents\My Games\Tabletop Simulator\Saves\Saved Objects\Language Pack German - Player Cards.json"
)
