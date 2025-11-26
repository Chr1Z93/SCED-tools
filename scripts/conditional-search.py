# Filters files with a FILTER_STRING and a NOT_FILTER_STRING

import os

# Config
SEARCH_FOLDER = r"C:\git\SCED"

# must be part of file
FILTER_STRING = '"startsInPlay": true'

# must not be part of file
NOT_FILTER_STRING = '"permanent": true,'

# Loop through files
for root, dirs, files in os.walk(SEARCH_FOLDER):
    if ".git" in dirs:
        dirs.remove(".git")

    if ".github" in dirs:
        dirs.remove(".github")

    if ".vscode" in dirs:
        dirs.remove(".vscode")

    for file in files:
        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if FILTER_STRING in content and NOT_FILTER_STRING not in content:
                print(f"Matched: {file_path}")

        except Exception as e:
            print(f"Error at {file_path}: {e}")
