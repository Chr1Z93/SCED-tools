import json
from pathlib import Path

script_path = Path(__file__).parent.resolve()
project_path = Path(r"C:\git\SCED-downloads\decomposed\campaign\Dark Matter")


def get_fp_and_metadata(file_path):
    if not file_path.is_file():
        return None, None

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, None

    # Get image information from the main JSON
    custom_deck = data.get("CustomDeck", {})

    face_url = None
    back_url = None
    index = None

    if custom_deck:
        deck = next(iter(custom_deck.values()))
        face_url = deck.get("FaceURL")
        back_url = deck.get("BackURL")

        card_id = data.get("CardID")
        if card_id is not None:
            index = card_id % 100

    # Get metadata
    gmnotes_file = file_path.with_suffix(".gmnotes")

    if gmnotes_file.exists():
        try:
            metadata = json.loads(gmnotes_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            metadata = None
    else:
        raw_notes = data.get("GMNotes", "")

        if raw_notes:
            try:
                metadata = json.loads(raw_notes)
            except json.JSONDecodeError:
                metadata = None
        else:
            metadata = None

    return (face_url, back_url, index), metadata


def create_mapping():
    mapping = {}

    for file_path in project_path.rglob("*"):
        if not file_path.is_file():
            continue

        fp, metadata = get_fp_and_metadata(file_path)
        if not fp or not isinstance(metadata, dict) or "id" not in metadata:
            continue

        face_url, back_url, index = fp

        if not face_url or not back_url or index is None:
            continue

        # JSON cannot use tuples as keys, so create a string fingerprint
        fingerprint = f"{face_url}|{back_url}|{index}"
        if fingerprint in mapping:
            continue

        mapping[fingerprint] = metadata["id"]

    print(f"Project contains {len(mapping)} different cards.")

    output_file = script_path / "image-id-mapping.json"
    output_file.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(f"Image to ID mapping successfully created.")


if __name__ == "__main__":
    create_mapping()
