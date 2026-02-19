import json

INPUT_FILE = r"C:\Users\pulsc\Downloads\reprint_data.json"
OUTPUT_FILE = r"C:\git\SCED\src\playercards\ReprintGroups.ttslua"


def export_reprint_map_to_lua(json_file_path, output_file_path):
    with open(json_file_path, "r") as f:
        raw_data = json.load(f)

    # Dictionary to hold the groups: {id: set_of_related_ids}
    groups = {}

    for entry in raw_data["data"]["all_card"]:
        code = entry["code"]
        dup_of = entry["duplicate_of_code"]

        # Union-Find logic: Merge sets so all related IDs are in one group
        group_a = groups.get(code, {code})
        group_b = groups.get(dup_of, {dup_of})
        union_group = group_a.union(group_b)

        for member in union_group:
            groups[member] = union_group

    # Generate Lua Table string
    lua_lines = ["-- Reprint Data (used as basis for the fallback system for language packs)", "REPRINT_GROUPS = {"]

    for card_id in sorted(groups.keys()):
        # Convert set to list and sort so the 'Original' IDs typically come first
        siblings = sorted(list([m for m in groups[card_id] if m != card_id]))
        siblings_str = ", ".join([f'"{s}"' for s in siblings])
        lua_lines.append(f'  ["{card_id}"] = {{ {siblings_str} }},')

    lua_lines.append("}")

    # Write to file
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lua_lines) + "\n")

    print(f"Successfully exported to {output_file_path}")


# Run the export
export_reprint_map_to_lua(INPUT_FILE, OUTPUT_FILE)
