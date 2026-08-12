import json
import os
from pathlib import Path

script_path = Path(__file__).parent.resolve()

# Correct Shoggoth project
source_project_path = script_path / "alice_en.json"

# Previous version of the Shoggoth project
target_project_path = script_path / "alice_de.json"

# TTS export to update
tts_project_path = Path(
    r"C:\git\SCED-downloads\decomposed\language-pack\German - Fan Campaigns\German-FanCampaigns.GermanFC\AliceinWonderland.08d1cc"
)


def load_json(path: Path) -> dict:
    """Load a JSON file and return its contents."""
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def update_tts_ids():
    # -------------------------------------------------------------------------
    # Validate input files
    # -------------------------------------------------------------------------

    if not source_project_path.is_file():
        raise FileNotFoundError(f"Source project not found:\n{source_project_path}")

    if not target_project_path.is_file():
        raise FileNotFoundError(f"Target project not found:\n{target_project_path}")

    if not tts_project_path.is_dir():
        raise FileNotFoundError(f"TTS project directory not found:\n{tts_project_path}")

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
    # Build project number -> new ID mapping
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

    # Duplicates make the mapping ambiguous, so abort rather than guessing.
    if duplicate_project_numbers:
        duplicates = ", ".join(duplicate_project_numbers)

        raise ValueError(
            "Duplicate project numbers found in source project:\n" f"{duplicates}"
        )

    # Missing IDs indicate invalid source data.
    if missing_source_ids:
        missing = ", ".join(missing_source_ids)

        raise ValueError("Source cards have a project_number but no ID:\n" f"{missing}")

    # -------------------------------------------------------------------------
    # Build old ID -> new ID mapping
    # -------------------------------------------------------------------------

    id_map = {}

    missing_project_number = 0
    project_number_not_found = 0
    duplicate_old_ids = []

    for card in target_project["cards"]:
        project_number = card.get("project_number")
        old_id = card.get("id")

        if not project_number:
            missing_project_number += 1
            continue

        if old_id is None:
            continue

        project_number = str(project_number)

        if project_number not in project_number_to_id:
            project_number_not_found += 1
            continue

        new_id = project_number_to_id[project_number]

        # Detect an old ID being associated with different new IDs.
        if old_id in id_map and id_map[old_id] != new_id:
            duplicate_old_ids.append(old_id)
            continue

        id_map[old_id] = new_id

    if duplicate_old_ids:
        conflicts = ", ".join(map(str, duplicate_old_ids))

        raise ValueError("Old IDs map to multiple new IDs:\n" f"{conflicts}")

    # -------------------------------------------------------------------------
    # Update TTS project cards
    # -------------------------------------------------------------------------

    updated = 0
    already_correct = 0
    not_found = 0
    missing_id = 0
    invalid_metadata = 0
    non_card_files = 0

    for root, dirs, files in os.walk(tts_project_path):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = Path(root) / filename

            try:
                data = load_json(file_path)
            except (json.JSONDecodeError, OSError):
                invalid_metadata += 1
                continue

            # Skip non-card objects.
            if data.get("Name") not in ["Card", "CardCustom"]:
                non_card_files += 1
                continue

            # Read the existing GMNotes.
            try:
                metadata = json.loads(data.get("GMNotes", ""))
            except (json.JSONDecodeError, TypeError):
                invalid_metadata += 1
                continue

            old_id = metadata.get("id")

            if old_id is None:
                missing_id += 1
                continue

            # No mapping means this card wasn't present in the previous
            # Shoggoth project, or its ID doesn't belong to this migration.
            if old_id not in id_map:
                not_found += 1
                continue

            new_id = id_map[old_id]

            # Nothing to change.
            if old_id == new_id:
                already_correct += 1
                continue

            # Update only the ID.
            metadata["id"] = new_id

            # Store the updated GMNotes.
            data["GMNotes"] = json.dumps(
                metadata,
                ensure_ascii=False,
                separators=(",", ":"),
            )

            # Write the file back.
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")

            updated += 1

    # -------------------------------------------------------------------------
    # Report
    # -------------------------------------------------------------------------

    print()
    print("Finished.")
    print()
    print("Shoggoth mapping:")
    print(f"  Source cards:             {len(source_project['cards'])}")
    print(f"  Previous cards:           {len(target_project['cards'])}")
    print(f"  ID mappings:              {len(id_map)}")
    print(f"  Missing project number:   {missing_project_number}")
    print(f"  Project number unknown:   {project_number_not_found}")
    print()
    print("TTS project:")
    print(f"  Updated:                  {updated}")
    print(f"  Already correct:          {already_correct}")
    print(f"  ID not found:             {not_found}")
    print(f"  Missing ID:               {missing_id}")
    print(f"  Invalid metadata:         {invalid_metadata}")
    print(f"  Non-card files:           {non_card_files}")


if __name__ == "__main__":
    update_tts_ids()
