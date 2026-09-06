import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ARKHAM_BUILD_PATH = Path(
    r"C:\git\SCED-tools\scripts\shoggoth-tools\ab_dark_matter.json"
)
TTS_FOLDER = Path(r"C:\git\SCED-downloads\decomposed\campaign\The Path to Carcosa")
SHOGGOTH_PATH = Path(r"C:\git\darkMatter\project.json")
TRANSLATION_PATHS = [
    Path(r"C:\git\darkMatter\project_de.json"),
    Path(r"C:\git\darkMatter\project_fr.json"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def remove_formatting_tags(text: str) -> str:
    """Remove HTML/XML-like formatting tags from a card name."""
    return re.sub(r"</?[^>]+>", "", text)


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=4)
        f.write("\n")


def load_tts_metadata(file_path: Path, data: dict) -> dict | None:
    """
    Load TTS GMNotes metadata.

    First try the GMNotes field. If that is empty or invalid, try a
    sidecar .gmnotes file with the same base name.
    """

    # Try GMNotes field first
    gmnotes = data.get("GMNotes")

    if gmnotes:
        try:
            return json.loads(gmnotes)
        except (json.JSONDecodeError, TypeError):
            pass

    # Try sidecar .gmnotes file
    gmnotes_path = file_path.with_suffix(".gmnotes")

    if gmnotes_path.exists():
        try:
            with open(gmnotes_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"TTS ERROR: Could not read metadata " f"{gmnotes_path}: {e}")

    return None


# ---------------------------------------------------------------------------
# Step 1: Build canonical ID map from arkham.build / TTS
# ---------------------------------------------------------------------------


def build_canonical_id_map(
    arkham_build_path: Path,
) -> dict[tuple[str, str], str]:
    """
    Build (card name, subtitle) -> canonical ID from an arkham.build project.
    """

    print("=" * 60)
    print("STEP 1: Loading arkham.build project")
    print("=" * 60)

    project = load_json(arkham_build_path)
    cards = project.get("data", {}).get("cards", [])
    name_to_ids: dict[tuple[str, str], set[str]] = {}

    for card in cards:
        name = card.get("name")
        subname = card.get("subname", "")
        card_id = card.get("code")

        if not name:
            print("ARKHAM.BUILD ERROR: Card without name")
            continue

        if not card_id:
            print(f"ARKHAM.BUILD ERROR: No code for '{name}'")
            continue

        # Ignore back-side cards
        if card_id.endswith("-back"):
            continue

        name = remove_formatting_tags(name.strip())
        subname = remove_formatting_tags(subname.strip())
        key = (name, subname)
        name_to_ids.setdefault(key, set()).add(card_id)

    # Resolve duplicates
    name_to_id: dict[tuple[str, str], str] = {}

    for key, ids in name_to_ids.items():
        if len(ids) == 1:
            name_to_id[key] = next(iter(ids))
        else:
            name, subname = key
            display_name = name

            if subname:
                display_name += f" — {subname}"

            print(
                f"ARKHAM.BUILD CONFLICT: '{display_name}' has multiple IDs: "
                f"{', '.join(sorted(ids))}"
            )

    print()
    print(f"Cards in arkham.build: {len(cards)}")
    print(f"Unique name/subtitle combinations: {len(name_to_id)}")
    print(f"Conflicting combinations: " f"{len(name_to_ids) - len(name_to_id)}")

    return name_to_id


def add_tts_cards_to_canonical_id_map(
    tts_folder: Path,
    canonical_id_map: dict[tuple[str, str], str],
):
    """
    Add cards from the decomposed TTS project to the canonical ID map.

    TTS:
        Name == "Card" or "CardCustom"
        Nickname -> card name
        Description -> subtitle
        metadata["id"] -> canonical ID
    """

    print()
    print("=" * 60)
    print("STEP 1B: Loading Tabletop Simulator project")
    print("=" * 60)

    name_to_ids: dict[tuple[str, str], set[str]] = {}

    files_processed = 0
    cards_found = 0
    errors = 0

    for file_path in tts_folder.rglob("*.json"):
        files_processed += 1

        try:
            data = load_json(file_path)
        except (json.JSONDecodeError, OSError) as e:
            print(f"TTS ERROR: Could not read {file_path}: {e}")
            errors += 1
            continue

        # Only process Card / CardCustom objects
        if data.get("Name") not in ("Card", "CardCustom"):
            continue

        cards_found += 1

        name = data.get("Nickname", "").strip()

        if not name:
            print(f"TTS ERROR: Card without name: {file_path}")
            errors += 1
            continue

        # Assuming Description contains the subtitle.
        subtitle = data.get("Description", "") or ""
        subtitle = subtitle.strip()

        name = remove_formatting_tags(name)
        subtitle = remove_formatting_tags(subtitle)
        metadata = load_tts_metadata(file_path, data)

        if metadata is None:
            print(f"TTS ERROR: No valid metadata: {file_path}")
            errors += 1
            continue

        card_id = metadata.get("id")

        if not card_id:
            print(f"TTS ERROR: No ID in metadata: {file_path}")
            errors += 1
            continue

        key = (name, subtitle)

        name_to_ids.setdefault(key, set()).add(card_id)

    # Add TTS IDs to the canonical map.
    added = 0
    conflicts = 0

    for key, ids in name_to_ids.items():
        name, subtitle = key

        if len(ids) > 1:
            display_name = name

            if subtitle:
                display_name += f" — {subtitle}"

            print(
                f"TTS CONFLICT: '{display_name}' has multiple IDs: "
                f"{', '.join(sorted(ids))}"
            )
            conflicts += 1
            continue

        tts_id = next(iter(ids))

        # If the same card was already found in arkham.build,
        # check whether the IDs agree.
        if key in canonical_id_map:
            existing_id = canonical_id_map[key]

            if existing_id != tts_id:
                display_name = name

                if subtitle:
                    display_name += f" — {subtitle}"

                print(
                    f"SOURCE CONFLICT: '{display_name}'\n"
                    f"    arkham.build: {existing_id}\n"
                    f"    TTS:          {tts_id}"
                )
                conflicts += 1

                # Don't overwrite the existing canonical ID.
                continue

            # Same ID from both sources, nothing to do.
            continue

        canonical_id_map[key] = tts_id
        added += 1

    print()
    print(f"TTS JSON files processed: {files_processed}")
    print(f"TTS cards found:          {cards_found}")
    print(f"TTS cards added:          {added}")
    print(f"TTS conflicts:            {conflicts}")
    print(f"TTS errors:               {errors}")


# ---------------------------------------------------------------------------
# Step 2: Update main Shoggoth project
# ---------------------------------------------------------------------------


def update_shoggoth_project(
    project: dict,
    canonical_id_map: dict[tuple[str, str], str],
) -> dict[str, str]:
    """
    Update the IDs in the main Shoggoth project.
    Matching is performed using: (card name, subtitle)
    Returns a mapping:

        old Shoggoth ID -> new canonical ID

    This mapping is required to update the translation files because their
    card IDs are used as dictionary keys.
    """

    print()
    print("=" * 60)
    print("STEP 2: Updating Shoggoth project")
    print("=" * 60)

    cards = project.get("cards", [])
    id_mapping: dict[str, str] = {}

    updated = 0
    unchanged = 0
    not_found = 0
    missing_id = 0

    for card in cards:
        name = card.get("name")
        subtitle = card.get("front", {}).get("subtitle", "") or ""

        if not name:
            print("SHOGGOTH ERROR: Card without name")
            continue

        name = remove_formatting_tags(name.strip())
        subtitle = remove_formatting_tags(subtitle.strip())

        old_id = card.get("id")

        if not old_id:
            print(f"SHOGGOTH ERROR: No ID for '{name}'")
            missing_id += 1
            continue

        key = (name, subtitle)
        new_id = canonical_id_map.get(key)

        if new_id is None:
            if subtitle:
                print(f"NOT-FOUND: {name} — {subtitle}")
            else:
                print(f"NOT-FOUND: {name}")

            not_found += 1
            continue

        # Always remember the relationship
        id_mapping[old_id] = new_id

        if old_id == new_id:
            unchanged += 1
            continue

        card["id"] = new_id
        updated += 1

    print()
    print("Shoggoth update finished.")
    print(f"Updated:     {updated}")
    print(f"Unchanged:   {unchanged}")
    print(f"Not found:   {not_found}")
    print(f"Missing ID:  {missing_id}")
    print(f"ID mappings: {len(id_mapping)}")

    return id_mapping


# ---------------------------------------------------------------------------
# Step 3: Update translation file
# ---------------------------------------------------------------------------


def update_translation_file(
    translation_path: Path,
    id_mapping: dict[str, str],
):
    """
    Update the IDs used as keys in a Shoggoth translation file.

    The translated card data itself is left untouched.

    Example:

        "old-id": {
            "name": "...",
            ...
        }

    becomes:

        "new-id": {
            "name": "...",
            ...
        }
    """

    print()
    print("=" * 60)
    print(f"TRANSLATION: {translation_path.name}")
    print("=" * 60)

    translation = load_json(translation_path)
    cards = translation.get("cards")

    if not isinstance(cards, dict):
        print("ERROR: Translation file has no valid 'cards' dictionary.")
        return

    updated = 0
    unchanged = 0
    not_found = 0
    conflicts = 0

    new_cards = {}

    for old_id, card_data in cards.items():

        # No ID mapping exists for this translation entry
        if old_id not in id_mapping:
            not_found += 1

            # Keep the original entry so we don't accidentally delete data
            new_cards[old_id] = card_data
            continue

        new_id = id_mapping[old_id]

        # The ID did not change
        if old_id == new_id:
            unchanged += 1
            new_cards[old_id] = card_data
            continue

        # Check whether another translation entry already uses the new ID
        if new_id in new_cards:
            conflicts += 1

            # Keep the old entry rather than losing data
            new_cards[old_id] = card_data
            continue

        new_cards[new_id] = card_data
        updated += 1

    translation["cards"] = new_cards

    print()
    print(f"Updated:     {updated}")
    print(f"Unchanged:   {unchanged}")
    print(f"Not found:   {not_found}")
    print(f"Conflicts:   {conflicts}")

    save_json(translation_path, translation)
    print(f"Saved: {translation_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def update_ids():
    # -----------------------------------------------------------------------
    # Step 1
    # -----------------------------------------------------------------------

    canonical_id_map = build_canonical_id_map(ARKHAM_BUILD_PATH)
    add_tts_cards_to_canonical_id_map(TTS_FOLDER, canonical_id_map)

    # -----------------------------------------------------------------------
    # Step 2
    # -----------------------------------------------------------------------

    print()
    print("Loading Shoggoth project...")

    shoggoth_project = load_json(SHOGGOTH_PATH)
    id_mapping = update_shoggoth_project(shoggoth_project, canonical_id_map)

    # Save main project
    save_json(SHOGGOTH_PATH, shoggoth_project)

    print()
    print(f"Saved: {SHOGGOTH_PATH}")

    # -----------------------------------------------------------------------
    # Step 3
    # -----------------------------------------------------------------------

    for translation_path in TRANSLATION_PATHS:
        if not translation_path.exists():
            print()
            print(f"TRANSLATION ERROR: File does not exist: " f"{translation_path}")
            continue

        update_translation_file(translation_path, id_mapping)

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    update_ids()
