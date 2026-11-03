import json
import os

TARGET_FOLDER = (
    r"C:\git\SCED-downloads\decomposed\campaign\Bloodborne - City of the Unseen"
)

# This is needed for TARGET_FOLDERs with incomplete metadata (e.g. Language Packs)
SOURCE_FOLDER = None


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

        # Skip sideways cards (they should be scaled correctly)
        if data.get("SidewaysCard"):
            return False

        if "Transform" in data:
            data["Transform"]["scaleX"] = 0.8214 / 1.15
            data["Transform"]["scaleZ"] = 0.8214 / 1.15
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            return True
    except Exception:
        return False
    return False


def get_act_agenda_ids(source_folder):
    act_agenda_ids = set()
    for root, _, files in os.walk(source_folder):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)
            meta = get_metadata_obj(file_path)
            if str(meta.get("type", "")) in ("Act", "Agenda"):
                id = meta.get("id", meta.get("TtsZoopGuid"))
                if id:
                    act_agenda_ids.add(id)

    return act_agenda_ids


def main():
    source_ids = get_act_agenda_ids(SOURCE_FOLDER) if SOURCE_FOLDER else None
    cards_updated = 0
    decks_updated = set()  # Use a set to avoid counting the same deck multiple times

    for root, dirs, files in os.walk(TARGET_FOLDER):
        for filename in files:
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(root, filename)

            try:
                meta = get_metadata_obj(file_path)
                if source_ids is None:
                    is_act_or_agenda = str(meta.get("type", "")) in ("Act", "Agenda")
                else:
                    card_id = meta.get("id", meta.get("TtsZoopGuid"))
                    is_act_or_agenda = card_id in source_ids

                if not is_act_or_agenda:
                    continue

                # Update the Card
                if update_transform(file_path):
                    cards_updated += 1
                    print(f"Updated Card: {filename}")

                # Check the Container
                parent_dir_name = os.path.basename(root)
                container_json_path = os.path.join(
                    os.path.dirname(root), parent_dir_name + ".json"
                )

                if container_json_path in decks_updated or not os.path.exists(
                    container_json_path
                ):
                    continue

                with open(container_json_path, "r", encoding="utf-8") as cf:
                    container_data = json.load(cf)

                if container_data.get("Name") == "Deck" and update_transform(
                    container_json_path
                ):
                    decks_updated.add(container_json_path)
                    print(f"   -> Parent container '{parent_dir_name}' updated.")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    # --- Final Summary ---
    print("\n" + "=" * 30)
    print("PROCESSING COMPLETE")
    print("=" * 30)
    print(f"Total Cards Updated:  {cards_updated}")
    print(f"Total Decks Updated:  {len(decks_updated)}")
    print("=" * 30)


if __name__ == "__main__":
    main()
