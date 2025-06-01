import os

# Config
search_folder = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German\LanguagePackGerman.3ac577"
excluded_folder = r"C:\git\SCED-downloads\decomposed\campaign\Language Pack German\LanguagePackGerman.3ac577\Grundspiel.3c77b5"
filter_string = "https://steamusercontent-a.akamaihd.net/ugc/1833529903258581968/029B34E50FFF71F1AA6E4EBE4A451986E0B3A51B/"

# Normalize excluded path for comparison
excluded_folder = os.path.normpath(excluded_folder)

# Loop through files
for root, dirs, files in os.walk(search_folder):
    # Skip excluded folder
    if os.path.commonpath([os.path.normpath(root), excluded_folder]) == excluded_folder:
        continue

    for file in files:
        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if filter_string in content:
                print(f"Deleting: {file_path}")
                os.remove(file_path)

        except Exception as e:
            print(f"Error at {file_path}: {e}")
