import json
import os

# Use a global constant for the input file path
INPUT_FILE = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German - Campaigns\LanguagePackGerman-Campaigns.GermanC\AmRandederWelt.f4f47a.json"


def increase_number(item_string):
    """Increases the first numerical part of a string by 500 and returns the updated string."""
    if "." in item_string:
        parts = item_string.split(".")
        number_part = int(parts[0])
        if int(parts[0][-3]) < 5:
            mod = 500
        if parts[0][0] == "0":
            start = "0"
        else:
            start = ""

        if parts[2]:
            return start + str(number_part + mod) + "." + parts[1] + "." + parts[2]
        else:
            return start + str(number_part + mod) + "." + parts[1]

    else:
        number_part = int(item_string)
        if int(item_string[-3]) < 5:
            mod = 500
        if item_string[0] == "0":
            start = "0"
        else:
            start = ""
        return start + str(number_part + mod)


def update_json_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "ContainedObjects_order" in data and isinstance(
        data["ContainedObjects_order"], list
    ):
        updated_list = []
        for item in data["ContainedObjects_order"]:
            updated_item = increase_number(item)
            updated_list.append(updated_item)

        data["ContainedObjects_order"] = updated_list
        print(f"Updated 'ContainedObjects_order' in: {file_path}")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")


def update_json_files_in_folder(folder_path):
    """Renames the files and updates the 'Nickname' fields."""
    if not os.path.isdir(folder_path):
        print(f"Error: The directory {folder_path} was not found.")
        return

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["Nickname"] = increase_number(data["Nickname"])

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        # Rename the file after updating its content
        new_filename = increase_number(filename)
        old_file_path = os.path.join(folder_path, filename)
        new_file_path = os.path.join(folder_path, new_filename)

        os.rename(old_file_path, new_file_path)
        print(f"Processed file: {filename} -> {new_filename}")


def main():
    input_folder_path = os.path.splitext(INPUT_FILE)[0]
    update_json_data(INPUT_FILE)
    update_json_files_in_folder(input_folder_path)


if __name__ == "__main__":
    main()
