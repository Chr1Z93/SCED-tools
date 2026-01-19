import json
import os
import requests

# CONFIGURATION
INPUT_FOLDER_PATH = r"C:\git\SCED-downloads\decomposed"
API_URL = "https://api.arkham.build/v1/cache/cards/en"


def load_metadata():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return {
            item["id"]: item
            for item in response.json().get("data", {}).get("all_card", [])
        }
    except Exception as e:
        print(f"Error fetching metadata: {e}")
        return None


def update_gmnotes_logic(notes, metadata):
    """Updates the dictionary in-place. Returns True if changes were made."""
    card_id = notes.get("id")
    card_type = notes.get("type")

    if not card_id or card_type not in ["Act", "Agenda"]:
        return False

    local_meta = metadata.get(card_id)
    if not local_meta:
        return False

    if "clues" not in local_meta:
        return False

    if "clues_fixed" in local_meta:
        if notes.get("clueThreshold") == local_meta["clues"]:
            return False
        del notes["clueThresholdPerInvestigator"]
        notes["clueThreshold"] = local_meta["clues"]
    else:
        if notes.get("clueThresholdPerInvestigator") == local_meta["clues"]:
            return False
        del notes["clueThreshold"]
        notes["clueThresholdPerInvestigator"] = local_meta["clues"]

    return True


def process_recursive(root_folder, metadata):
    if not os.path.isdir(root_folder):
        print(f"Error: Directory {root_folder} not found.")
        return

    # os.walk travels through every subfolder
    for root, dirs, files in os.walk(root_folder):
        for filename in files:
            if not (filename.endswith(".gmnotes") or filename.endswith(".json")):
                continue

            file_path = os.path.join(root, filename)

            # Read the file
            with open(file_path, "r", encoding="utf-8", newline="") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue

            updated = False

            # Apply logic based on extension
            if filename.endswith(".gmnotes"):
                updated = update_gmnotes_logic(data, metadata)

            elif filename.endswith(".json") and "GMNotes" in data:
                try:
                    nested_notes = json.loads(data["GMNotes"])
                    if update_gmnotes_logic(nested_notes, metadata):
                        data["GMNotes"] = json.dumps(
                            nested_notes, indent=2, ensure_ascii=False
                        )
                        updated = True
                except (json.JSONDecodeError, TypeError):
                    continue

            # Write back only if changes occurred
            if updated:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                # Show relative path so you know which subfolder was updated
                rel_path = os.path.relpath(file_path, root_folder)
                print(f"✅ Updated: {rel_path}")


def main():
    metadata = load_metadata()
    if metadata:
        print("Metadata loaded. Starting recursive scan...")
        process_recursive(INPUT_FOLDER_PATH, metadata)
        print("Done!")
    else:
        print("Aborting: No metadata available.")


if __name__ == "__main__":
    main()
