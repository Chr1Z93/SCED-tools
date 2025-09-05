# Deletes all files that contain the FILTER_STRING in the SEARCH_FOLDER

import os

# Config
SEARCH_FOLDER = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German\LanguagePackGerman.3ac577"
EXCLUDED_FOLDER = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German\LanguagePackGerman.3ac577\Grundspiel.3c77b5"
FILTER_STRING = "https://steamusercontent-a.akamaihd.net/ugc/1833529903258581968/029B34E50FFF71F1AA6E4EBE4A451986E0B3A51B/"

# Normalize excluded path for comparison
EXCLUDED_FOLDER = os.path.normpath(EXCLUDED_FOLDER)

# Loop through files
for root, dirs, files in os.walk(SEARCH_FOLDER):
    if ".git" in dirs:
        dirs.remove(".git")

    if ".vscode" in dirs:
        dirs.remove(".vscode")

    # Skip excluded folder
    if os.path.commonpath([os.path.normpath(root), EXCLUDED_FOLDER]) == EXCLUDED_FOLDER:
        continue

    for file in files:
        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if FILTER_STRING in content:
                print(f"Deleting: {file_path}")
                os.remove(file_path)

        except Exception as e:
            print(f"Error at {file_path}: {e}")
