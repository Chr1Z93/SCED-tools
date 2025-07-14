# Filters files with a filter_string and then performs a search & replace on these files

import os

# Config
search_folder = r"C:\git\SCED-downloads"
original_string = '"PlayerCard"'
replacement_string = '"ScenarioCard"'
filter_string = "https://steamusercontent-a.akamaihd.net/ugc/2342503777940351785/F64D8EFB75A9E15446D24343DA0A6EEF5B3E43DB/"  # must be part of file

# Loop through files
# We use 'dirs' instead of '_' to access the list of directories
for root, dirs, files in os.walk(search_folder):
    if ".git" in dirs:
        dirs.remove(".git")

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
