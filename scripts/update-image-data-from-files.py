# This script will take a folder of images and update the accompanying card objects with the local file path

import json
import os

# --- Configuration ---
IMAGE_FOLDER = r"C:\Path\To\Your\Images"
DATA_FOLDER = r"C:\git\SCED\objects\AllPlayerCards"


def get_image_map(folder):
    """Creates a mapping of { 'arkham_id': 'Full_Path' } from the image folder."""
    image_map = {}
    valid_exts = (".jpg", ".jpeg", ".png", ".webp")

    if not os.path.exists(folder):
        print(f"Error: Image folder not found at {folder}")
        return image_map

    for filename in os.listdir(folder):
        if filename.lower().endswith(valid_exts):
            arkham_id = os.path.splitext(filename)[0]
            image_map[arkham_id] = os.path.join(folder, filename)
    return image_map


def extract_arkham_id_from_gmnotes_file(json_data, file_path):
    """Uses the GMNotes_path field to find and read the associated .gmnotes file."""
    if "GMNotes_path" not in json_data:
        return None

    # Split the path into (root, ext)
    root, ext = os.path.splitext(file_path)

    # Add the new extension
    gm_path = root + ".gmnotes"

    if os.path.exists(gm_path):
        try:
            with open(gm_path, "r", encoding="utf-8") as f:
                val = json.load(f).get("id")
                return str(val) if val is not None else None
        except (json.JSONDecodeError, IOError):
            pass
    return None


def main():
    image_map = get_image_map(IMAGE_FOLDER)
    if not image_map:
        print("No images found. Exiting.")
        return

    updated_count = 0

    for root, _, files in os.walk(DATA_FOLDER):
        for file_name in files:
            if not file_name.endswith(".json"):
                continue

            json_path = os.path.join(root, file_name)

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Get the ID using the GMNotes_path logic
            arkham_id = extract_arkham_id_from_gmnotes_file(data, json_path)

            if arkham_id and arkham_id in image_map:
                # Update FaceURL in all CustomDeck entries
                if "CustomDeck" not in data:
                    continue

                for deck_id in data["CustomDeck"]:
                    data["CustomDeck"][deck_id]["FaceURL"] = image_map[arkham_id]

                # Save changes back to the JSON
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.write("\n")

                updated_count += 1
                print(f"Updated {file_name} (Arkham ID: {arkham_id})")

    print("-" * 30)
    print(f"Done! Updated {updated_count} files.")


if __name__ == "__main__":
    main()
