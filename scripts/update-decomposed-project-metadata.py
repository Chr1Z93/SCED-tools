import json
import re
from pathlib import Path
from metadata_sorter import sortJSONKeys

# Paths config
CONTENT_PATH = Path(
    r"C:\git\SCED-downloads\decomposed\playercards\The Ghosts of Onigawa\TheGhostsofOnigawaInvestigatorExpansion.83a010"
)
SAVED_OBJECT_PATH = Path(
    r"C:\Users\Christian.Puls\Downloads\Ghosts of Onigawa Investigator Expansion-2026-07-09_07_27_23.json"
)
SET_CYCLE = "The Ghosts of Onigawa"


def clean_appendix(name_str):
    """Removes trailing numbers in parentheses like 'Destiny Bond (3)' -> 'Destiny Bond'."""
    # Matches a space followed by digits wrapped in parentheses at the very end of the string
    return re.sub(r"\s*\(\d+\)\s*$", "", name_str).strip()


def extract_appendix(name_str):
    """Extracts trailing numbers in parentheses like 'Destiny Bond (3)' -> ' (3)' or '' if missing."""
    match = re.search(r"\s*\(\d+\)\s*$", name_str)
    return match.group(0) if match else ""


def should_skip_by_tag(obj):
    """Returns True if 'Minicard' is present in the object's Tags."""
    tags = obj.get("Tags")
    if isinstance(tags, list):
        return any(str(tag).lower() == "minicard" for tag in tags)
    elif isinstance(tags, str):
        return tags.lower() == "minicard"
    return False


def build_metadata_map(obj, metadata_map):
    """Recursively crawls the saved object to map Nickname -> GMNotes string."""

    # Skip objects with "Minicard" tag
    if should_skip_by_tag(obj):
        # Still recurse into its children just in case it's a container tagged Minicard
        for child in obj.get("ContainedObjects", []):
            build_metadata_map(child, metadata_map)
        return

    # If the object has a Nickname and GMNotes, map it to its GMNotes string if not already mapped
    if "GMNotes" in obj and "Nickname" in obj:
        nickname = obj["Nickname"].strip().lower()
        raw_notes = obj["GMNotes"]
        if nickname and raw_notes != "":

            # Parse the JSON notes to inject the cycle attribute
            try:
                notes_json = json.loads(raw_notes)
                if isinstance(notes_json, dict):
                    notes_json["cycle"] = SET_CYCLE
                    sorted_metadata = sortJSONKeys(notes_json)

                    if nickname in metadata_map:
                        print(f"Warning: Multiple sets of metadata for {nickname}")
                    else:
                        metadata_map[nickname] = sorted_metadata

                    # Handle colon matching edge case: "Nickname: Description (Suffix)"
                    description = obj.get("Description", "").strip().lower()
                    if description != "":
                        base_nickname = clean_appendix(nickname)
                        suffix = extract_appendix(nickname)
                        
                        # Format: "name: description" or "name: description (3)"
                        combined_name = f"{base_nickname}: {description}{suffix}".strip()
                        
                        if combined_name not in metadata_map:
                            metadata_map[combined_name] = sorted_metadata
                else:
                    print(f"Issue with layout structure for: {nickname}")
            except json.JSONDecodeError:
                print(f"Error decoding GMNotes for: {nickname}")

    # Recurse deep into nested ContainedObjects (bags inside bags, decks, etc.)
    for child in obj.get("ContainedObjects", []):
        build_metadata_map(child, metadata_map)


def fill_no_level(metadata_map):
    current_nicknames = list(metadata_map.keys())
    for nickname in current_nicknames:
        no_level_name = clean_appendix(nickname)
        if no_level_name != nickname and no_level_name not in metadata_map:
            metadata_map[no_level_name] = metadata_map[nickname]


def update_metadata_target(json_file, file_data, new_gmnotes):
    """
    Overwrites the metadata target. If 'GMNotes_path' exists, it overwrites
    the external .gmnotes file as a formatted JSON object.
    Otherwise, it embeds the string directly into the internal 'GMNotes' field.
    """
    # Check if it uses an external .gmnotes path
    if "GMNotes_path" in file_data:
        gmnotes_file = json_file.with_suffix(".gmnotes")
        with open(gmnotes_file, "w", encoding="utf-8") as f:
            json.dump(new_gmnotes, f, indent=2, ensure_ascii=False)
            f.write("\n")

        return False
    else:
        # Internal replacement
        file_data["GMNotes"] = json.dumps(new_gmnotes, ensure_ascii=False)
        return True


def main():
    if not SAVED_OBJECT_PATH.exists():
        print(f"Error: Saved object not found at {SAVED_OBJECT_PATH}")
        return

    # 1. Load the Saved Object
    with open(SAVED_OBJECT_PATH, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    # 2. Build the map (Nickname -> Raw GMNotes String)
    metadata_map = {}
    root_obj = saved_data.get("ObjectStates", [saved_data])[0]
    build_metadata_map(root_obj, metadata_map)
    fill_no_level(metadata_map)

    print(f"Mapped {len(metadata_map)} unique Nicknames from Saved Object.")

    # Track matches and mismatches
    update_count = 0
    mismatched_cards = set()

    # 3. Loop through all JSON files in the content folder
    for json_file in CONTENT_PATH.rglob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                file_data = json.load(f)
            except json.JSONDecodeError:
                continue

        if file_data.get("Name") not in ["Card", "CardCustom"]:
            continue

        if should_skip_by_tag(file_data):
            continue

        # Look up match via Nickname
        card_name = file_data.get("Nickname", "").strip()
        if not card_name:
            continue

        card_name_lower = card_name.lower()

        if card_name_lower in metadata_map:
            new_metadata = metadata_map[card_name_lower]

            # Perform the injection/overwrite logic
            needs_rewrite = update_metadata_target(json_file, file_data, new_metadata)

            # Resave the core content JSON file to reflect internal changes (if needed)
            if needs_rewrite:
                with open(json_file, "w", encoding="utf-8") as f:
                    json.dump(file_data, f, indent=2, ensure_ascii=False)
                    f.write("\n")

            update_count += 1
        else:
            mismatched_cards.add(card_name)

    # 4. Print Summary Results
    print("--------------------------------------------------")
    print(f"Successfully updated {update_count} files in project.")
    print("--------------------------------------------------")

    if mismatched_cards:
        print(
            f"⚠️  {len(mismatched_cards)} Cards in content folder did not find a matching nickname:"
        )
        for name in sorted(mismatched_cards):
            print(f"  - {name}")
    else:
        print("✨ All content files successfully matched and updated!")
    print("--------------------------------------------------")


if __name__ == "__main__":
    main()
