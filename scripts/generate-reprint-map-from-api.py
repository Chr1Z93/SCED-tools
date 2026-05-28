import requests

ARKHAMBUILD_URL = "https://api-v2.arkham.build/v1/cache/cards"
OUTPUT_FILE = r"C:\git\SCED\src\playercards\ReprintGroups.ttslua"

DUPE_OVERRIDE = {"12031": "05024"}


def load_api_data():
    try:
        response = requests.get(ARKHAMBUILD_URL)
        response.raise_for_status()
        return response.json()["data"]["all_card"]

    except Exception as e:
        print(f"Error fetching card data: {e}")
        return None


def export_reprint_map_to_lua(card_data, output_file_path):
    # Dictionary to hold the groups: {id: set_of_related_ids}
    groups = {}

    for entry in card_data:
        code = entry["code"]

        if code in DUPE_OVERRIDE:
            entry["duplicate_of_code"] = DUPE_OVERRIDE[code]

        if "duplicate_of_code" not in entry or "taboo_set_id" in entry:
            continue

        dup_of = entry["duplicate_of_code"]

        # Union-Find logic: Merge sets so all related IDs are in one group
        group_a = groups.get(code, {code})
        group_b = groups.get(dup_of, {dup_of})
        union_group = group_a.union(group_b)

        for member in union_group:
            groups[member] = union_group

    # Generate Lua Table string
    lua_lines = [
        "-- Reprint Data (used as basis for the fallback system for language packs)",
        "REPRINT_GROUPS = {",
    ]

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


def main():
    card_data = load_api_data()
    export_reprint_map_to_lua(card_data, OUTPUT_FILE)


if __name__ == "__main__":
    main()
