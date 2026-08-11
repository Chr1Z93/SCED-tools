import json
import os
from pathlib import Path
import re

tts_folder = Path(
    r"C:\git\SCED-downloads\decomposed\language-pack\German - Fan Campaigns\German-FanCampaigns.GermanFC\AliceinWonderland.209aaa"
)
shoggoth_path = Path(r"C:\git\alice\project.json")


def remove_formatting_tags(text: str) -> str:
    return re.sub(r"</?[^>]+>", "", text)


def update_shoggoth_ids():
    # Build a map of:
    # German name -> set of all IDs found for that name
    german_name_to_ids = {}

    for root, dirs, files in os.walk(tts_folder):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Skip non-cards
            if data["Name"] not in ["Card", "CardCustom"]:
                continue

            try:
                metadata = json.loads(data.get("GMNotes", ""))
            except (json.JSONDecodeError, TypeError):
                print(f"Error in metadata for {filename}")
                continue

            name = data["Nickname"].strip()
            card_id = metadata.get("id")

            if not card_id:
                print(f"No ID found for {name}")
                continue

            german_name_to_ids.setdefault(name, set()).add(card_id)

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

    # Load the Shoggoth project
    with open(shoggoth_path, "r", encoding="utf-8") as f:
        project = json.load(f)

    # Loop through Shoggoth cards and update their IDs
    updated = 0
    not_found = 0
    conflicts = 0

    for card in project["cards"]:
        name = remove_formatting_tags(card["name"].strip())

        if name not in german_name_to_id:
            print(f"NOT-FOUND: {name}")
            not_found += 1
            continue

        new_id = german_name_to_id[name]

        if new_id == "CONFLICT":
            print(f"CONFLICT: {name}")
            conflicts += 1
            continue

        # Only update if the ID actually changed
        if card.get("id") != new_id:
            card["id"] = new_id
            updated += 1

    # Write the updated project back
    with open(shoggoth_path, "w", encoding="utf-8") as f:
        json.dump(project, f, ensure_ascii=True, indent=4)
        f.write("\n")

    print()
    print("Finished.")
    print(f"Updated:   {updated}")
    print(f"Not found: {not_found}")
    print(f"Conflicts: {conflicts}")


if __name__ == "__main__":
    update_shoggoth_ids()
