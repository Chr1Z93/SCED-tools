import json
from pathlib import Path

script_path = Path(__file__).parent.resolve()
source_project_path = script_path / "alice_en.json"
target_project_path = Path(r"C:\git\alice\project.json")


def update_shoggoth_ids():
    # Load the source Shoggoth project
    with open(source_project_path, "r", encoding="utf-8") as f:
        source_project = json.load(f)

    # Build a map of project number -> ID
    project_number_to_id = {}

    for card in source_project["cards"]:
        project_number = card.get("project_number")

        if project_number:
            project_number_to_id[project_number] = card.get("id")

    # Load the target Shoggoth project
    with open(target_project_path, "r", encoding="utf-8") as f:
        target_project = json.load(f)

    # Loop through Shoggoth cards and update their IDs
    updated = 0
    not_found = 0

    for card in target_project["cards"]:
        project_number = card.get("project_number")

        if not project_number or project_number not in project_number_to_id:
            not_found += 1
            continue

        new_id = project_number_to_id[project_number]

        # Only update if the ID actually changed
        if card.get("id") != new_id:
            card["id"] = new_id
            updated += 1

    # Write the updated project back
    with open(target_project_path, "w", encoding="utf-8") as f:
        json.dump(target_project, f, ensure_ascii=True, indent=4)
        f.write("\n")

    print()
    print("Finished.")
    print(f"Updated:   {updated}")
    print(f"Not found: {not_found}")


if __name__ == "__main__":
    update_shoggoth_ids()
