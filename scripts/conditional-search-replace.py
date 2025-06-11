# Filters files with a filter_string and then performs a search & replace on these files

import os

# Config
search_folder = r"C:\git\SCED-downloads\decomposed\campaign\The Circle Undone"
original_string = '"cycle": "The Circle Undone"'
replacement_string = '"cycle": "Core"'
filter_string = '"id": "01'  # must be part of file

# Loop through files
for root, _, files in os.walk(search_folder):
    for file in files:
        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if filter_string in content:
                new_content = content.replace(original_string, replacement_string)

                if new_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Replaced in: {file_path}")

        except Exception as e:
            print(f"Error at {file_path}: {e}")
