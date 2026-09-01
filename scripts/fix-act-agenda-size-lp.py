import os
import json

ORIGINAL_PATH = r"C:\git\SCED-downloads\decomposed\campaign\Alice in Wonderland"
LANGUAGEPACK_PATH = r"C:\git\SCED-downloads\decomposed\language-pack\German - Fan Campaigns\German-FanCampaigns.GermanFC\AliceinWonderland.08d1cc"


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
            data["Transform"]["scaleX"] = 0.8214 / 1.15
            data["Transform"]["scaleZ"] = 0.8214 / 1.15
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            return True
    except Exception:
        return False
    return False


# Create a set of all Act / Agenda IDs
act_agenda_set = set()
for root, dirs, files in os.walk(ORIGINAL_PATH):
    for filename in files:
        if filename.endswith(".json"):
            file_path = os.path.join(root, filename)
            meta = get_metadata_obj(file_path)
            meta_type = str(meta.get("type", ""))

            if meta_type in ["Act", "Agenda"] and "TtsZoopGuid" in meta:
                act_agenda_set.add(meta.get("TtsZoopGuid"))


# --- Counters for Summary ---
cards_updated = 0

for root, dirs, files in os.walk(LANGUAGEPACK_PATH):
    for filename in files:
        if filename.endswith(".json"):
            file_path = os.path.join(root, filename)

            try:
                meta = get_metadata_obj(file_path)
                id = meta.get("id", meta.get("TtsZoopGuid"))

                if id in act_agenda_set:
                    if update_transform(file_path):
                        cards_updated += 1
                        print(f"Updated Card: {filename}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")

# --- Final Summary ---
print("\n" + "=" * 30)
print("PROCESSING COMPLETE")
print("=" * 30)
print(f"Total Cards Updated:  {cards_updated}")
print("=" * 30)
