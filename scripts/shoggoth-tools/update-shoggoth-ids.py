import json
import os
from pathlib import Path

tts_folder = Path(
    r"C:\git\SCED-downloads\decomposed\language-pack\German - Fan Campaigns\German-FanCampaigns.GermanFC\AliceinWonderland.209aaa"
)
shoggoth_path = Path(r"C:\git\alice\project.json")


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
                print(f"Erorr in metadata for {filename}")
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

    # Loop through shoggoth cards and update their IDs
    updated = 0
    not_found = 0
    conflicts = 0

    # ???
    
    print()
    print("Finished.")
    print(f"Updated:   {updated}")
    print(f"Not found: {not_found}")
    print(f"Conflicts: {conflicts}")


if __name__ == "__main__":
    update_shoggoth_ids()
