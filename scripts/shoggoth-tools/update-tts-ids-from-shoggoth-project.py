import json
import re
from pathlib import Path

CARD_TYPES = {"Card", "CardCustom"}

# Shoggoth project
shoggoth_project_path = Path(r"C:\git\darkMatter\project.json")

# TTS project
tts_project_path = Path(
    r"C:\git\SCED-downloads\decomposed\campaign\Dark Matter\DarkMatter.d713f4"
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_name(name: str) -> str:
    """Make Shoggoth markup and TTS display names comparable."""
    return re.sub(r"</?[^>]+>", "", name).strip()


def build_name_to_id(project: dict) -> dict[str, object]:
    if "cards" not in project:
        raise ValueError("Shoggoth project does not contain a 'cards' field.")

    name_to_id = {}
    duplicate_names = set()

    for card in project["cards"]:
        name = card.get("name")
        card_id = card.get("id")

        if not name:
            continue

        normalized_name = normalize_name(name)

        if normalized_name in name_to_id:
            duplicate_names.add(normalized_name)
            continue

        name_to_id[normalized_name] = card_id

    if duplicate_names:
        duplicates = ", ".join(sorted(duplicate_names))
        print(f"Duplicate card names found in Shoggoth project:\n{duplicates}")

    return name_to_id


def update_tts_ids(shoggoth_path: Path, tts_folder: Path) -> None:
    if not shoggoth_path.is_file():
        raise FileNotFoundError(f"Shoggoth project not found:\n{shoggoth_path}")

    if not tts_folder.is_dir():
        raise FileNotFoundError(f"TTS project directory not found:\n{tts_folder}")

    shoggoth_project = load_json(shoggoth_path)
    name_to_id = build_name_to_id(shoggoth_project)

    updated = 0
    already_correct = 0
    not_found = 0
    missing_name = 0
    invalid_metadata = 0

    for file_path in sorted(tts_folder.rglob("*.json")):
        try:
            data = load_json(file_path)
        except (json.JSONDecodeError, OSError):
            invalid_metadata += 1
            continue

        if data.get("Name") not in CARD_TYPES:
            continue

        name = data.get("Nickname")
        if not isinstance(name, str) or not name.strip():
            missing_name += 1
            continue

        normalized_name = normalize_name(name)
        if normalized_name not in name_to_id:
            not_found += 1
            print(f"NOT-FOUND: {name}")
            continue

        try:
            metadata = json.loads(data.get("GMNotes", ""))
        except (json.JSONDecodeError, TypeError):
            invalid_metadata += 1
            continue

        if not isinstance(metadata, dict):
            invalid_metadata += 1
            continue

        new_id = name_to_id[normalized_name]
        old_id = metadata.get("id")

        if old_id == new_id:
            already_correct += 1
            continue

        metadata["id"] = new_id
        data["GMNotes"] = json.dumps(
            metadata,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        with file_path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")

        updated += 1

    print()
    print("Finished.")
    print()
    print("Shoggoth project:")
    print(f"  Cards with unique names: {len(name_to_id)}")
    print()
    print("TTS project:")
    print(f"  Updated:                 {updated}")
    print(f"  Already correct:         {already_correct}")
    print(f"  Name not found:          {not_found}")
    print(f"  Missing name:            {missing_name}")
    print(f"  Invalid metadata:        {invalid_metadata}")


if __name__ == "__main__":
    update_tts_ids(shoggoth_project_path, tts_project_path)
