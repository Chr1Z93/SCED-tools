import json
import os
from pathlib import Path

english_folder = Path(
    r"C:\git\SCED-downloads\decomposed\campaign\Alice in Wonderland\AliceinWonderland.39916d"
)
german_folder = Path(
    r"C:\git\SCED-downloads\decomposed\language-pack\German - Fan Campaigns\German-FanCampaigns.GermanFC\AliceinWonderland.209aaa"
)
script_path = Path(__file__).parent.resolve()
name_map_path = script_path / "alice_mapping.json"

prefixes = (
    "Act 1 - ",
    "Act 2 - ",
    "Act 3 -",
    "Agenda 1 - ",
    "Agenda 2 - ",
    "Agenda 3 -",
)


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
    # Load existing map of English name -> German name
    with open(name_map_path, "r", encoding="utf-8") as f:
        english_to_german_name = json.load(f)

    # Build a map of:
    # German name -> set of all IDs found for that name
    german_name_to_ids = {}

    for root, dirs, files in os.walk(english_folder):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Skip non-cards
            if data["Name"] not in ["Card", "CardCustom"]:
                continue

            metadata = get_metadata_obj(file_path, data)
            name = data["Nickname"]

            # Clean up name
            for prefix in prefixes:
                if name.startswith(prefix):
                    name = name[len(prefix) :]
                    break

            if name not in english_to_german_name:
                print(f"No translation found for {name}")
                continue

            german_name = english_to_german_name[name]
            card_id = metadata.get("id", metadata.get("TtsZoopGuid"))

            if not card_id:
                print(f"No ID found for {name}")
                continue

            german_name_to_ids.setdefault(german_name, set()).add(card_id)

    # Convert the sets into the final lookup:
    #   German name -> ID
    #   German name -> "CONFLICT" if multiple IDs exist
    german_name_to_id = {}

    for german_name, ids in german_name_to_ids.items():
        if len(ids) == 1:
            german_name_to_id[german_name] = next(iter(ids))
        else:
            german_name_to_id[german_name] = "CONFLICT"
            print(f"CONFLICT for '{german_name}': " f"{', '.join(sorted(ids))}")

    # Loop through German cards and update their IDs
    updated = 0
    not_found = 0
    conflicts = 0

    for root, dirs, files in os.walk(german_folder):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = Path(root) / filename

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Skip non-cards
            if data["Name"] not in ["Card", "CardCustom"]:
                continue

            german_name = data["Nickname"]

            if german_name not in german_name_to_id:
                new_id = "NOT-FOUND"
                not_found += 1
                print(f"NOT-FOUND: {german_name}")
            else:
                new_id = german_name_to_id[german_name]

                if new_id == "CONFLICT":
                    conflicts += 1
                    print(f"CONFLICT: {german_name}")

            # Read the existing GMNotes
            try:
                metadata = json.loads(data.get("GMNotes", ""))
            except (json.JSONDecodeError, TypeError):
                metadata = {}

            # Update only the ID
            metadata["id"] = new_id

            # Store the updated GMNotes
            data["GMNotes"] = json.dumps(
                metadata,
                ensure_ascii=False,
                separators=(",", ":"),
            )

            # Write the file back
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")

            updated += 1

    print()
    print("Finished.")
    print(f"Updated:   {updated}")
    print(f"Not found: {not_found}")
    print(f"Conflicts: {conflicts}")


if __name__ == "__main__":
    update_tts_ids()
