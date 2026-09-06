import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ARKHAM_BUILD_PATH = Path(r"C:\Users\pulsc\Downloads\ab_dark_matter.json")
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


# ---------------------------------------------------------------------------
# Step 1: Build canonical ID map from arkham.build
# ---------------------------------------------------------------------------


def build_canonical_id_map(arkham_build_path: Path) -> dict[str, str]:
    """
    Build card name -> canonical ID from an arkham.build project.
    """

    print("=" * 60)
    print("STEP 1: Loading arkham.build project")
    print("=" * 60)

    project = load_json(arkham_build_path)
    cards = project.get("data", {}).get("cards", [])
    name_to_ids: dict[str, set[str]] = {}

    for card in cards:
        name = card.get("name")
        card_id = card.get("code")

        if not name:
            print("ARKHAM.BUILD ERROR: Card without name")
            continue

        if not card_id:
            print(f"ARKHAM.BUILD ERROR: No code for '{name}'")
            continue

        name = remove_formatting_tags(name.strip())
        name_to_ids.setdefault(name, set()).add(card_id)

    # Resolve duplicates
    name_to_id: dict[str, str] = {}

    for name, ids in name_to_ids.items():
        if len(ids) == 1:
            name_to_id[name] = next(iter(ids))
        else:
            print(
                f"ARKHAM.BUILD CONFLICT: '{name}' has multiple IDs: "
                f"{', '.join(sorted(ids))}"
            )

    print()
    print(f"Cards in arkham.build: {len(cards)}")
    print(f"Unique card names:     {len(name_to_id)}")
    print(f"Conflicting names:     {len(name_to_ids) - len(name_to_id)}")

    return name_to_id


# ---------------------------------------------------------------------------
# Step 2: Update main Shoggoth project
# ---------------------------------------------------------------------------


def update_shoggoth_project(
    project: dict,
    canonical_id_map: dict[str, str],
) -> dict[str, str]:
    """
    Update the IDs in the main Shoggoth project.

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

        if not name:
            print("SHOGGOTH ERROR: Card without name")
            continue

        name = remove_formatting_tags(name.strip())
        old_id = card.get("id")

        if not old_id:
            print(f"SHOGGOTH ERROR: No ID for '{name}'")
            missing_id += 1
            continue

        new_id = canonical_id_map.get(name)

        if new_id is None:
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

    # -----------------------------------------------------------------------
    # Step 2
    # -----------------------------------------------------------------------

    print()
    print("Loading Shoggoth project...")

    shoggoth_project = load_json(SHOGGOTH_PATH)

    id_mapping = update_shoggoth_project(
        shoggoth_project,
        canonical_id_map,
    )

    # Save main project
    save_json(
        SHOGGOTH_PATH,
        shoggoth_project,
    )

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

        update_translation_file(
            translation_path,
            id_mapping,
        )

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    update_ids()
