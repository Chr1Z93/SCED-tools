import json
from pathlib import Path

script_path = Path(__file__).parent.resolve()
mapping1_path = script_path / "image-id-mapping-old.json"
mapping2_path = script_path / "image-id-mapping-new.json"

target_path = Path(
    r"C:\git\SCED-downloads\decomposed\language-pack\Russian - Fan Campaigns\Russian-FanCampaigns.RussianFC\DarkMatter.d713f4"
)


def load_mapping(file_path):
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_id_mapping(mapping1, mapping2):
    id_mapping = {}

    for fingerprint, id1 in mapping1.items():
        id2 = mapping2.get(fingerprint)

        if id2 is None:
            continue

        if id1 in id_mapping and id_mapping[id1] != id2:
            print(f"Conflicting mapping for {id1}:")
            print(f"  Existing: {id_mapping[id1]}")
            print(f"  New:      {id2}")
            continue

        id_mapping[id1.lower()] = id2

    return id_mapping


def update_file(file_path, id_mapping):
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    raw_notes = data.get("GMNotes")

    if not raw_notes:
        return False

    try:
        metadata = json.loads(raw_notes)
    except json.JSONDecodeError:
        return False

    old_id = metadata.get("id", "").lower()

    if old_id not in id_mapping:
        return False

    new_id = id_mapping[old_id]

    if old_id == new_id:
        return False

    metadata["id"] = new_id
    data["GMNotes"] = json.dumps(
        metadata,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    file_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"{file_path.name}: {old_id} -> {new_id}")
    return True


def update_folder(target_path, id_mapping):
    updated = 0

    for file_path in target_path.rglob("*.json"):
        if update_file(file_path, id_mapping):
            updated += 1

    print(f"Updated {updated} files.")


def main():
    mapping1 = load_mapping(mapping1_path)
    mapping2 = load_mapping(mapping2_path)

    id_mapping = create_id_mapping(mapping1, mapping2)

    print(f"Created {len(id_mapping)} ID mappings.")

    output_path = script_path / "id-mapping.json"
    output_path.write_text(
        json.dumps(id_mapping, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    print(f"ID mapping written to {output_path}")

    update_folder(target_path, id_mapping)


if __name__ == "__main__":
    main()
