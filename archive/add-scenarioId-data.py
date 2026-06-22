from pathlib import Path
import re
import requests

LUA_FILE_PATH = Path(r"C:\git\SCED\src\playarea\PlayAreaImageData.ttslua")
API_URL = "https://api.arkham.build/v1/cache/cards/en"


def load_metadata():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()

        cards = response.json().get("data", {}).get("all_card", [])

        name_to_id_map = {}
        for item in cards:
            # 1. Filter strictly for scenario reference cards
            if item.get("type_code") != "scenario":
                continue

            name = item.get("real_name")
            card_id = item.get("id")

            # 2. Normalize name format to lowercase and strip whitespaces
            # ensuring it seamlessly matches what clean_lua_name outputs
            cleaned_name = name.strip().lower()
            name_to_id_map[cleaned_name] = card_id

        print(f"Successfully cached {len(name_to_id_map)} scenario mapping references.")
        return name_to_id_map

    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return None


def clean_lua_name(str_input):
    # 1. remove prefix type 1: str:gsub("%w+%-%w%s%-%s", "")
    # Matches alphanumeric-alphanumeric followed by a space, hyphen, space (e.g., "II-B - ")
    str_input = re.sub(r"^\w+-\w\s-\s", "", str_input)

    # 2. remove prefix type 2: str:gsub("%w+%-%w%s", "")
    # Matches alphanumeric-alphanumeric followed by a space (e.g., "59-Z ")
    str_input = re.sub(r"^\w+-\w\s", "", str_input)

    # 3. remove prefix type 3: str:gsub("%w+%s%-%s", "")
    # Matches alphanumeric followed by space, hyphen, space (e.g., "III - ")
    str_input = re.sub(r"^\w+\s-\s", "", str_input)

    # 4. remove prefix type 4: str:gsub("%?+%s%-%s", "")
    # Matches literal question marks followed by space, hyphen, space (e.g., "??? - ")
    str_input = re.sub(r"^\?+\s-\s", "", str_input)

    # 5. remove suffix (numbering): str:gsub("%s%d+", "")
    # Matches a space followed by one or more digits at the end of the string
    str_input = re.sub(r"\s\d+$", "", str_input)

    # Return lowercase and stripped to match the ArkhamDB API mapping
    return str_input.strip().lower()


def update_lua_file():
    # 1. Get the database mapping (now formatted as name -> id)
    metadata = load_metadata()
    if not metadata:
        print("Could not retrieve metadata mapping. Aborting script execution.")
        return

    # 2. Read your current Lua file
    with open(LUA_FILE_PATH, "r", encoding="utf-8") as f:
        lua_content = f.read()

    # 3. Regex block finder
    pattern = r"(\{\s*Name\s*=\s*\"([^\"]+)\",\s*URL\s*=\s*\"([^\"]+)\"\s*\})"

    def replacer(match):
        full_block = match.group(1)
        raw_name = match.group(2)

        # Clean the name to match Arkham conventions
        lookup_name = clean_lua_name(raw_name)
        card_id = metadata.get(lookup_name)

        if card_id:
            # Inject the ID field right before the Name field, matching indentation style
            updated_block = full_block.replace("{", f'{{\n        ID = "{card_id}",', 1)
            print(f"Matched: '{raw_name}' -> ID: {card_id}")
            return updated_block
        else:
            # If no ID is found, we fall back to a generated slug or leave a warning comment
            fallback_slug = raw_name.lower().replace(" ", "_").replace("-", "")
            print(f"⚠️  No match found for '{raw_name}' (Used fallback slug)")
            return full_block.replace(
                "{", f'{{\n        ID = "{fallback_slug}", -- FIXME', 1
            )

    # 4. Process the replacements
    updated_content = re.sub(pattern, replacer, lua_content)

    # 5. Save the output directly back over the file path
    with open(LUA_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"\nDone! Updated file saved to: {LUA_FILE_PATH}")


if __name__ == "__main__":
    update_lua_file()
