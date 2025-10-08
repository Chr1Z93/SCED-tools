import os
import json

# --- Configuration ---
TARGET_DIRECTORY = r"C:\git\SCED-downloads\decomposed"


def sort_json_keys_recursively(root_folder_path):
    """
    Recursively loops through all .json files in the root folder and its subfolders,
    sorts their keys alphabetically, and only overwrites the original file
    if the content has changed.

    :param root_folder_path: The path to the folder to start searching from.
    """
    if not os.path.isdir(root_folder_path):
        print(f"Error: Folder not found at '{root_folder_path}'")
        return

    print(f"Starting recursive key sort in folder: {root_folder_path}")
    processed_count = 0
    written_count = 0

    # os.walk() iterates through directories, subdirectories, and files
    for dirpath, _, filenames in os.walk(root_folder_path):
        print(f"Processing: {dirpath}")
        for filename in filenames:
            if filename.endswith(".json"):
                file_path = os.path.join(dirpath, filename)

                try:
                    # 1. Read the ORIGINAL content as a string
                    with open(file_path, "r", encoding="utf-8") as f:
                        original_content = f.read()

                    # 2. Load the JSON object from the string
                    data = json.loads(original_content)

                    # 3. Generate the NEW, sorted JSON content string
                    new_sorted_content = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)

                    # 4. Compare the original content to the new content
                    if original_content.strip() != new_sorted_content.strip():
                        # 5. Write the NEW content back if a change was detected
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_sorted_content + "\n")
                        written_count += 1

                    processed_count += 1


                except json.JSONDecodeError:
                    print(f"Skipped: {filename} - Invalid JSON format.")
                except IOError as e:
                    print(f"Error processing {filename}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred with {filename}: {e}")

    print("=" * 70)
    print(f"Finished processing. Total files checked: {processed_count}")
    print(f"Total files updated (content changed): {written_count}")


if __name__ == "__main__":
    sort_json_keys_recursively(TARGET_DIRECTORY)
