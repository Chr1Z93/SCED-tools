# Filters files with a FILTER_STRING and then performs a search & replace on these files

import os

# Config
SEARCH_FOLDER = r"C:\git\SCED-downloads"
ORIGINAL_STRING = '"PlayerCard"'
REPLACEMENT_STRING = '"ScenarioCard"'
FILTER_STRING = "https://steamusercontent-a.akamaihd.net/ugc/2342503777940351785/F64D8EFB75A9E15446D24343DA0A6EEF5B3E43DB/"  # must be part of file

# Loop through files
for root, dirs, files in os.walk(SEARCH_FOLDER):
    if ".git" in dirs:
        dirs.remove(".git")

    if ".vscode" in dirs:
        dirs.remove(".vscode")

    for file in files:
        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if FILTER_STRING in content:
                new_content = content.replace(ORIGINAL_STRING, REPLACEMENT_STRING)

                if new_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Replaced in: {file_path}")

        except Exception as e:
            print(f"Error at {file_path}: {e}")
