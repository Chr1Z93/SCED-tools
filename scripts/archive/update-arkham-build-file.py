import json
import re

# This regex matches any Unicode whitespace character (\s) 
# at the start (^) or end ($) of the string.
unicode_strip = re.compile(r"^[\s\u200b\u200e\u00a0]+|[\s\u200b\u200e\u00a0]+$")

def get_tts_data_recursive(objects_list, tts_map):
    """Recursively crawls TTS objects to build the name-to-data map."""
    for obj in objects_list:
        raw_name = obj.get("Nickname")
        if raw_name and raw_name != "":
            clean_name = raw_name.strip().lower()

            gm_notes_raw = obj.get("GMNotes", "{}")
            try:
                gm_notes = json.loads(gm_notes_raw)
            except json.JSONDecodeError:
                gm_notes = {}

            custom_deck = obj.get("CustomDeck", {})
            if custom_deck:
                deck_info = next(iter(custom_deck.values()))
                tts_map[clean_name] = {
                    "card_id": gm_notes.get("id", gm_notes.get("TtsZoopGuid")),
                    "face_url": deck_info.get("FaceURL"),
                    "back_url": deck_info.get("BackURL"),
                }

        # If this object contains other objects (like a Bag or Deck), recurse
        if "ContainedObjects" in obj:
            get_tts_data_recursive(obj["ContainedObjects"], tts_map)


def sync_deck_data(file_a_path, file_b_path, output_path):
    with open(file_a_path, "r", encoding="utf-8") as f:
        data_a = json.load(f)
    with open(file_b_path, "r", encoding="utf-8") as f:
        data_b = json.load(f)

    # --- PASS 1: Build Lookup (Recursive) ---
    tts_map = {}
    get_tts_data_recursive([data_a], tts_map)

    # Update a.b file
    id_translation_map = {}
    cards_list = data_b.get("data", {}).get("cards", [])

    for card in cards_list:
        name = unicode_strip.sub("", card.get("name")).lower()
        if "xp" in card and card["xp"] > 0:
            name_with_level = f"{name} ({card["xp"]})"
        else:
            name_with_level = f"{name}"

        old_code = card.get("code")

        # We only map the "base" ID (ignoring -back for the map creation)
        if name_with_level in tts_map:
            source = tts_map[name_with_level]
            new_code = source["card_id"]

            if old_code and new_code and old_code != new_code:
                # If the current card is a 'back' side, we don't want to
                # map the '-back' string as the key, just the GUID.
                base_old_id = old_code.replace("-back", "")
                id_translation_map[base_old_id] = new_code

            if new_code and "code" in card:
                card["code"] = card["code"].replace(base_old_id, new_code)

            if source["face_url"] and "image_url" in card:
                card["image_url"] = source["face_url"]
            if source["back_url"] and "back_image_url" in card:
                card["back_image_url"] = source["back_url"]
        else:
            print(f"DEBUG: No match for '{name_with_level}'")

    # --- PASS 2: Update References (Requirements, Back Links, Suffixed Codes) ---
    ref_fields = ["deck_requirements", "back_link", "restrictions"]
    update_counts = {field: 0 for field in ref_fields}

    for card in cards_list:
        for field in ref_fields:
            val = card.get(field)
            if val and isinstance(val, str):
                new_val = val
                for old_id, new_id in id_translation_map.items():
                    if old_id in new_val:
                        new_val = new_val.replace(old_id, new_id)

                if new_val != val:
                    card[field] = new_val
                    update_counts[field] += 1

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_b, f, indent=2, ensure_ascii=False)

    print(f"--- Sync Report ---")
    print(f"ID mappings created: {len(id_translation_map)}")
    for field, count in update_counts.items():
        print(f"Field '{field}' updates: {count}")
    print(f"-------------------")


# Run it
sync_deck_data(
    r"C:\git\SCED-downloads\downloadable\playercards\kaimonogatari_investigator_expansion.json",
    r"C:\Users\pulsc\Downloads\Kaimonogatari.json",
    r"C:\Users\pulsc\Downloads\Kaimonogatari_updated.json",
)
