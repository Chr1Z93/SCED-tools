import os
import json

# --- CONFIGURATION ---
TARGET_DIRECTORY = r"C:\git\SCED-downloads\decomposed"
IDS_DIRECTORY = r"C:\Users\pulsc\Downloads\core encounter sets\single sided"
NEW_FACE_URL = "https://steamusercontent-a.akamaihd.net/ugc/13243700374285212184/EA0A1926B70F720CDBC4EDC375FE76BD22E17389/"
NEW_BACK_URL = "https://steamusercontent-a.akamaihd.net/ugc/2342503777940351785/F64D8EFB75A9E15446D24343DA0A6EEF5B3E43DB/"
DECK_PREFIX = "100"  # The first part of the CardID and the CustomDeck key


def get_valid_ids(folder_path):
    """Returns a SORTED list of IDs to ensure the 00-99 suffix is consistent."""
    valid_ids = []
    if not os.path.exists(folder_path):
        return valid_ids
    for filename in os.listdir(folder_path):
        name_only = os.path.splitext(filename)[0]
        if name_only:
            valid_ids.append(name_only)

    # print(f"Loaded {len(valid_ids)} IDs.")

    # Sorting ensures that 'id_a' always gets 00 and 'id_b' always gets 01
    return sorted(valid_ids)


def update_json_data(data, index):
    """
    Applies the specific CardID and CustomDeck logic.
    index: the integer position (0, 1, 2...) from the valid_ids list.
    """
    # Create the 2-digit suffix (e.g., 0 -> "00", 1 -> "01")
    suffix = f"{index:02}"

    # Update CardID (e.g., "2317" + "00" = 231700)
    data["CardID"] = int(f"{DECK_PREFIX}{suffix}")

    # Update CustomDeck
    # We create a new dict to replace the old one entirely
    data["CustomDeck"] = {
        DECK_PREFIX: {
            "BackIsHidden": True,
            "BackURL": NEW_BACK_URL,
            "FaceURL": NEW_FACE_URL,
            "NumHeight": 4,
            "NumWidth": 7,
            "Type": 0,
        }
    }
    return data


def process_json_files():
    valid_ids = get_valid_ids(IDS_DIRECTORY)

    # Convert list to a dictionary for O(1) lookup of the index: { "id_name": index }
    id_map = {name: i for i, name in enumerate(valid_ids)}

    processed_count = 0
    last_output_count = 0
    match_count = 0

    for root, dirs, files in os.walk(TARGET_DIRECTORY):
        for file in files:
            if not file.lower().endswith(".json"):
                continue

            processed_count += 1

            if processed_count > (last_output_count + 500):
                last_output_count = processed_count
                print(
                    f"Progress: Scanned {processed_count} files, updated {match_count} files."
                )

            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Skipping {file}: Error reading JSON ({e})")
                continue

            # Check for GMNotes or GMNotes_path
            gm_notes_raw = None

            if data.get("GMNotes"):
                gm_notes_raw = data["GMNotes"]
            elif data.get("GMNotes_path"):
                # Construct path to the .gmnotes file
                base_path = os.path.splitext(file_path)[0]
                gm_notes_file = base_path + ".gmnotes"

                if os.path.exists(gm_notes_file):
                    with open(gm_notes_file, "r", encoding="utf-8") as gmf:
                        gm_notes_raw = gmf.read()

            # Skip if no notes found or string is empty
            if not gm_notes_raw or str(gm_notes_raw).strip() == "":
                continue

            # Load the internal GMNotes JSON string
            try:
                gm_notes_data = json.loads(gm_notes_raw)
            except (json.JSONDecodeError, TypeError):
                # If it's not a valid JSON string, we skip it
                continue

            # Check for the "id" field in the inner GMNotes
            inner_id = gm_notes_data.get("id")

            if inner_id not in id_map:
                continue

            match_count += 1

            # Perform the Update
            current_index = id_map[inner_id]
            updated_data = update_json_data(data, current_index)

            # Save the file back
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(updated_data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            # print(f"Successfully updated: {file} (ID: {inner_id})")

    print(f"Done! Scanned {processed_count} files, updated {match_count} files.")


if __name__ == "__main__":
    process_json_files()
