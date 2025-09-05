import json
import os

INPUT_FILE = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German - Campaigns\LanguagePackGerman-Campaigns.GermanC\AmRandederWelt.f4f47a.json"


def update_json_data(file_path):
    """
    Loads a JSON file, updates the 'ContainedObjects_order' list,
    and saves the changes back to the file.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "ContainedObjects_order" in data and isinstance(
            data["ContainedObjects_order"], list
        ):
            updated_list = []
            for item in data["ContainedObjects_order"]:
                # Replace the old number with the new one
                updated_item = item.replace(increaseNumber(item))
                updated_list.append(updated_item)

            data["ContainedObjects_order"] = updated_list
            print(f"Updated 'ContainedObjects_order' in: {file_path}")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    except FileNotFoundError:
        print(f"Error: The file {file_path} was not found.")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}.")
    except Exception as e:
        print(f"An unexpected error occurred while processing {file_path}: {e}")


def increaseNumber(item):
    parts = item.split(".")
    number_part = int(parts[0])
    updated_number = str(number_part + 500)
    return updated_number + "." + parts[1]


def update_json_files_in_folder(folder_path):
    """
    Updates JSON files within a specified folder. For each file,
    it renames the file and updates the 'Nickname' field inside it.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: The directory {folder_path} was not found.")
        return

    for filename in os.listdir(folder_path):
        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(folder_path, filename)

        # Update the nickname field inside the JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        with open(file_path, "w", encoding="utf-8") as f:
            data["Nickname"] = increaseNumber(data["Nickname"])
            json.dump(
                data,
                f,
                indent=2,
                separators=(",", ": "),
                ensure_ascii=False,
            )
            f.write("\n")

        # Rename the file
        new_filename = increaseNumber(filename)

        old_file_path = os.path.join(folder_path, filename)
        new_file_path = os.path.join(folder_path, new_filename)

        os.rename(old_file_path, new_file_path)
        print(f"Processed file: {filename} -> {new_filename}")


def main():
    # Extract the directory path from the input file path
    input_folder_path = os.path.splitext(INPUT_FILE)[0]

    # Process the main JSON file
    update_json_data(INPUT_FILE)

    print("\n--- Processing sub-folder files ---\n")

    # Process JSON files in the corresponding sub-folder
    update_json_files_in_folder(input_folder_path)


if __name__ == "__main__":
    main()
