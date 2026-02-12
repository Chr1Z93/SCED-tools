import os

# Config
SEARCH_FOLDER = r"C:\git\SCED"

# All of these must be present in the file
INCLUDE_FILTERS = ['"alternate_ids":', '"cycle": "Core"']

# None of these can be present in the file (leave empty [] if none)
EXCLUDE_FILTERS = []

# Folders to skip during the walk
SKIP_DIRS = {".git", ".github", ".vscode"}

# Initialize counter
match_count = 0

# Loop through files
for root, dirs, files in os.walk(SEARCH_FOLDER):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for file in files:
        file_path = os.path.join(root, file)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            must_have = all(s in content for s in INCLUDE_FILTERS)
            must_not_have = any(s in content for s in EXCLUDE_FILTERS)

            if must_have and not must_not_have:
                print(f"Matched: {file_path}")
                match_count += 1  # Increment the counter

        except Exception as e:
            print(f"Error at {file_path}: {e}")

# Final Summary
print("-" * 30)
print(f"Done! Matched {match_count} files.")
