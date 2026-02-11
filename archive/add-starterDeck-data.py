import os
import json
from pathlib import Path
import re

LUA_SOURCE_FILE = Path(r"C:\git\SCED\src\playercards\PlayerCardPanelData.ttslua")
SEARCH_FOLDER = Path(r"C:\git\SCED\objects")


def add_field(starter_deck_data, json_file_path: Path):
    with open(json_file_path, "r", encoding="utf-8") as f_json:
        json_data = json.load(f_json)

    starter_deck_id = starter_deck_data.get(json_data.get("Nickname"))
    if not starter_deck_id:
        return

    gm_notes_path = json_data.get("GMNotes_path")
    if gm_notes_path and gm_notes_path != "":
        abs_path = SEARCH_FOLDER / gm_notes_path

        # Correctly read the JSON file content before loading it
        with open(abs_path, "r", encoding="utf-8") as g_json:
            metadata = json.load(g_json)

        if metadata.get("type") != "Investigator":
            return

        metadata["starterDeck"] = starter_deck_id

        with open(abs_path, "w", encoding="utf-8") as g_json:
            json.dump(metadata, g_json, indent=2)
            g_json.write("\n")


def update_metadata(starter_deck_data):
    for root, _, files in os.walk(SEARCH_FOLDER):
        for file_name in files:
            if file_name.endswith(".json"):
                json_file_path = Path(root) / file_name
                add_field(starter_deck_data, json_file_path)


def collect_starter_deck_data():
    starter_deck_data = {}

    with open(LUA_SOURCE_FILE, "r", encoding="utf-8") as f_lua:
        lua_content = f_lua.read()

    # Regex to find investigator blocks and capture the name and starterDeck value
    # It looks for: INVESTIGATORS["Name"] = { ... starterDeck = "ID" ... }
    pattern = re.compile(
        r'INVESTIGATORS\["([^"]+)"\]\s*=\s*{.*?starterDeck\s*=\s*"([^"]+)"', re.DOTALL
    )

    matches = pattern.finditer(lua_content)
    for match in matches:
        investigator_name = match.group(1)
        starter_deck_id = match.group(2)
        starter_deck_data[investigator_name] = starter_deck_id

    return starter_deck_data


if __name__ == "__main__":
    starter_deck_data = collect_starter_deck_data()
    update_metadata(starter_deck_data)
