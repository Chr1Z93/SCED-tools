import os
import json

FOLDER_PATH = (
    r"C:\git\SCED-downloads\decomposed\campaign\Bloodborne - City of the Unseen"
)


def get_metadata_obj(file_path):
    base_name = os.path.splitext(file_path)[0]
    gmnotes_file = base_name + ".gmnotes"

    if os.path.exists(gmnotes_file):
        with open(gmnotes_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                raw_notes = data.get("GMNotes", "")
                if isinstance(raw_notes, str) and (
                    raw_notes.startswith("{") or raw_notes.startswith("[")
                ):
                    return json.loads(raw_notes)
                return {"type": raw_notes}
            except (json.JSONDecodeError, TypeError):
                return {}
    return {}


def update_transform(file_path):
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "Transform" in data:
            data["Transform"]["scaleX"] = 0.8214
            data["Transform"]["scaleZ"] = 0.8214
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            return True
    except Exception:
        return False
    return False


# --- Counters for Summary ---
cards_updated = 0
decks_updated = set()  # Use a set to avoid counting the same deck multiple times

for root, dirs, files in os.walk(FOLDER_PATH):
    for filename in files:
        if filename.endswith(".json"):
            file_path = os.path.join(root, filename)

            try:
                meta = get_metadata_obj(file_path)
                meta_type = str(meta.get("type", ""))

                if meta_type in ["Act", "Agenda"] and "TtsZoopGuid" in meta:
                    # Update the Card
                    if update_transform(file_path):
                        cards_updated += 1
                        print(f"Updated Card: {filename}")

                    # Check the Container
                    parent_dir_path = root
                    parent_dir_name = os.path.basename(parent_dir_path)
                    grandparent_dir = os.path.dirname(parent_dir_path)
                    container_json_path = os.path.join(
                        grandparent_dir, parent_dir_name + ".json"
                    )

                    if os.path.exists(container_json_path):
                        with open(container_json_path, "r", encoding="utf-8") as cf:
                            container_data = json.load(cf)

                        if container_data.get("Name") == "Deck":
                            if update_transform(container_json_path):
                                decks_updated.add(container_json_path)
                                print(
                                    f"   -> Parent container '{parent_dir_name}' updated."
                                )

            except Exception as e:
                print(f"Error processing {filename}: {e}")

# --- Final Summary ---
print("\n" + "=" * 30)
print("PROCESSING COMPLETE")
print("=" * 30)
print(f"Total Cards Updated:  {cards_updated}")
print(f"Total Decks Updated:  {len(decks_updated)}")
print("=" * 30)
