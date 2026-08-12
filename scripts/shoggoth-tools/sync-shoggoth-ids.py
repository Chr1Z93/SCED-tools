import json
from pathlib import Path

script_path = Path(__file__).parent.resolve()
source_project_path = script_path / "alice_en.json"
target_project_path = Path(r"C:\git\alice\project.json")


def load_json(path: Path) -> dict:
    """Load a JSON file and return its contents."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def update_shoggoth_ids():
    # -------------------------------------------------------------------------
    # Validate input files
    # -------------------------------------------------------------------------

    if not source_project_path.is_file():
        raise FileNotFoundError(f"Source project not found:\n{source_project_path}")

    if not target_project_path.is_file():
        raise FileNotFoundError(f"Target project not found:\n{target_project_path}")

    # -------------------------------------------------------------------------
    # Load projects
    # -------------------------------------------------------------------------

    source_project = load_json(source_project_path)
    if "cards" not in source_project:
        raise ValueError("Source project does not contain a 'cards' field.")

    target_project = load_json(target_project_path)
    if "cards" not in target_project:
        raise ValueError("Target project does not contain a 'cards' field.")

    # -------------------------------------------------------------------------
    # Build project number -> ID mapping
    # -------------------------------------------------------------------------

    project_number_to_id = {}
    duplicate_project_numbers = []
    missing_source_ids = []

    for card in source_project["cards"]:
        project_number = card.get("project_number")
        card_id = card.get("id")

        if not project_number:
            continue

        project_number = str(project_number)

        if card_id is None:
            missing_source_ids.append(project_number)
            continue

        if project_number in project_number_to_id:
            duplicate_project_numbers.append(project_number)
            continue

        project_number_to_id[project_number] = card_id

    # Duplicates make the mapping ambiguous, so abort rather than guessing
    if duplicate_project_numbers:
        duplicates = ", ".join(map(str, duplicate_project_numbers))

        raise ValueError(
            "Duplicate project numbers found in source project:\n" f"{duplicates}"
        )

    # Missing IDs also indicate invalid source data
    if missing_source_ids:
        missing = ", ".join(map(str, missing_source_ids))

        raise ValueError("Source cards have a project_number but no ID:\n" f"{missing}")

    # -------------------------------------------------------------------------
    # Update IDs
    # -------------------------------------------------------------------------

    updated = 0
    already_correct = 0
    missing_project_number = 0
    project_number_not_found = 0

    for card in target_project["cards"]:
        project_number = card.get("project_number")

        if not project_number:
            missing_project_number += 1
            continue

        project_number = str(project_number)

        if project_number not in project_number_to_id:
            project_number_not_found += 1
            continue

        new_id = project_number_to_id[project_number]

        if card.get("id") == new_id:
            already_correct += 1
            continue

        card["id"] = new_id
        updated += 1

    # -------------------------------------------------------------------------
    # Write updated project
    # -------------------------------------------------------------------------

    with target_project_path.open("w", encoding="utf-8") as f:
        json.dump(target_project, f, ensure_ascii=True, indent=4)

    # -------------------------------------------------------------------------
    # Report
    # -------------------------------------------------------------------------

    print()
    print("Finished.")
    print()
    print(f"Source cards:           {len(source_project['cards'])}")
    print(f"Target cards:           {len(target_project['cards'])}")
    print()
    print(f"Updated:                {updated}")
    print(f"Already correct:        {already_correct}")
    print(f"Missing project number: {missing_project_number}")
    print(f"Project number unknown: {project_number_not_found}")


if __name__ == "__main__":
    update_shoggoth_ids()
