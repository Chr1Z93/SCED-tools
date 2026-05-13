import os
import json

TARGET_FOLDER = r"C:\git\SCED-downloads\decomposed\language-pack\Korean - Campaigns\Korean-Campaigns.KoreanC\TheFeastofHemlockVale.c740af"


def get_card_fingerprint(data):
    """Extracts the specific properties needed for comparison."""
    # Last two digits of CardID
    card_id_suffix = str(data.get("CardID", ""))[-2:]

    # URLs (Extracting from the first deck found in CustomDeck)
    face_url = ""
    back_url = ""
    custom_deck = data.get("CustomDeck", {})
    if custom_deck:
        first_deck = list(custom_deck.values())[0]
        face_url = first_deck.get("FaceURL", "")
        back_url = first_deck.get("BackURL", "")

    # GMNotes ID
    gm_id = ""
    gm_notes_str = data.get("GMNotes", "")
    if gm_notes_str:
        try:
            gm_data = json.loads(gm_notes_str)
            gm_id = gm_data.get("id", "")
        except json.JSONDecodeError:
            pass

    return {
        "id_suffix": card_id_suffix,
        "face": face_url,
        "back": back_url,
        "gm_id": gm_id,
    }


def clean_duplicates(folder):
    seen_exact = {}  # (suffix, face, back, gm_id) -> filename
    partial_matches = []
    to_remove = []

    files = [f for f in os.listdir(folder) if f.endswith(".json")]

    for filename in files:
        path = os.path.join(folder, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            fp = get_card_fingerprint(data)
            exact_key = (fp["id_suffix"], fp["face"], fp["back"], fp["gm_id"])

            # Check for Exact Duplicates
            if exact_key in seen_exact:
                to_remove.append(path)

                # Also check for .gmnotes to remove
                gm_path = path.replace(".json", ".gmnotes")
                if os.path.exists(gm_path):
                    to_remove.append(gm_path)
                continue

            # Check for Partial Matches (Conflicts)
            # We compare against already processed cards
            for other_key, other_file in seen_exact.items():
                other_suffix, other_face, other_back, other_gm = other_key

                img_match = (
                    fp["face"] == other_face
                    and fp["back"] == other_back
                    and fp["id_suffix"] == other_suffix
                )
                id_match = fp["gm_id"] == other_gm and fp["gm_id"] != ""

                if img_match != id_match:  # XOR: one matches but not both
                    partial_matches.append(
                        f"Conflict: {filename} <-> {other_file} (Img Match: {img_match}, ID Match: {id_match})"
                    )

            seen_exact[exact_key] = filename

        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # Remove Exact Duplicates
    removed_jsons = 0
    removed_gmnotes = 0
    for path in to_remove:
        filename = os.path.basename(path)

        # Detect extension before removing
        if filename.lower().endswith(".json"):
            removed_jsons += 1
        elif filename.lower().endswith(".gmnotes"):
            removed_gmnotes += 1

        os.remove(path)
        print(f"Deleted duplicate: {os.path.basename(path)}")

    # Report Conflicts
    if partial_matches:
        print("\n--- CONFLICTS FOUND (Manual Review Required) ---")
        for conflict in set(partial_matches):
            print(conflict)
    else:
        print("\nNo partial conflicts found.")

    # Summary
    print("\n" + "=" * 40)
    print(f"Duplicates removed (JSON): {removed_jsons}")
    print(f"Removed .gmnotes files):   {removed_gmnotes}")
    print(f"Total conflicts found:     {len(set(partial_matches))}")
    print("=" * 40)


if __name__ == "__main__":
    clean_duplicates(TARGET_FOLDER)
