# Updates a save file with data from arkham.build

import json


def update_json_data(to_edit_path, data_source_path, output_path):
    # 1. Load the data source and create a lookup map
    with open(data_source_path, "r", encoding="utf-8") as f:
        source_list = json.load(f)

    # Map key: (name, subname) -> value: new_id
    lookup = {
        (item["name"], item.get("subname", "")): item["code"] for item in source_list
    }

    # 2. Load the file to be edited
    with open(to_edit_path, "r", encoding="utf-8") as f:
        to_edit = json.load(f)

    def process_object(obj):
        # Check if this object meets your criteria
        is_card = obj.get("Name") == "Card"
        nickname = obj.get("Nickname")
        description = obj.get("Description", "")

        # Look for a match in our data source
        match_key = (nickname, description)

        if is_card and match_key in lookup:
            new_id = lookup[match_key]

            # Handle the stringified JSON in GMNotes
            try:
                gm_notes = json.loads(obj.get("GMNotes", "{}"))
                gm_notes["id"] = new_id
                # Optional: Update TtsZoopGuid if it exists and should match
                if "TtsZoopGuid" in gm_notes:
                    gm_notes["TtsZoopGuid"] = new_id

                obj["GMNotes"] = json.dumps(gm_notes)
                print(f"Updated: {nickname}")
            except json.JSONDecodeError:
                print(f"Warning: Could not parse GMNotes for {nickname}")

        # Recurse into ContainedObjects if they exist
        if "ContainedObjects" in obj and isinstance(obj["ContainedObjects"], list):
            for sub_obj in obj["ContainedObjects"]:
                process_object(sub_obj)

    # 3. Start processing (handling both single objects or lists at root)
    if isinstance(to_edit, list):
        for item in to_edit:
            process_object(item)
    else:
        process_object(to_edit)

    # 4. Save the result
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(to_edit, f, indent=2)
    print(f"\nProcessing complete. Saved to {output_path}")


# Run the script
update_json_data(
    r"C:\git\SCED-downloads\downloadable\campaign\night_of_vespers_campaign_expansion.json",
    r"C:\Users\pulsc\Downloads\input.json",
    r"C:\git\SCED-downloads\downloadable\campaign\night_of_vespers_campaign_expansion.json",
)
