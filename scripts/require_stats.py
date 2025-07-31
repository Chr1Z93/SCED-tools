import os
import re
from collections import defaultdict
from pathlib import Path

# Configuration: Path to your Tabletop Simulator project folders
PROJECT_FOLDER_1 = Path(r"C:\git\SCED")
PROJECT_FOLDER_2 = Path(r"C:\git\SCED-downloads")


def analyze_ttsl_requires(base_folder):
    counts = defaultdict(int)
    require_pattern = re.compile(r'require\("([^"]+)"\)')

    if not os.path.isdir(base_folder):
        print(f"Warning: Folder not found, skipping: {base_folder}")
        return counts

    for root, _, files in os.walk(base_folder):
        for file_name in files:
            if file_name.endswith((".lua", ".ttslua")):
                with open(Path(root) / file_name, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = require_pattern.findall(content)
                    for required_path in matches:
                        counts[required_path] += 1
    return counts


def output_ranking(title, counts):
    # Sort the combined results
    ranking = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    print(f"\n{title}")
    print("----------------------")

    for file_path, count in ranking:
        if count > 9:
            print(f"{count} - {file_path}")
        elif count > 1:
            print(f" {count} - {file_path}")


if __name__ == "__main__":
    total_counts = defaultdict(int)

    # Analyze Project Folder 1
    print(f"Scanning '{PROJECT_FOLDER_1}' for Lua/TTSLua file dependencies...")
    counts_folder_1 = analyze_ttsl_requires(PROJECT_FOLDER_1)
    for path, count in counts_folder_1.items():
        total_counts[path] += count

    # Analyze Project Folder 2
    print(f"Scanning '{PROJECT_FOLDER_2}' for Lua/TTSLua file dependencies...")
    counts_folder_2 = analyze_ttsl_requires(PROJECT_FOLDER_2)
    for path, count in counts_folder_2.items():
        total_counts[path] += count

    if not total_counts:
        print("No 'require' statements found in either specified folder.")
        exit()

    print("Info: Ranking excludes files that only occur once.")

    if counts_folder_1:
        output_ranking(f"{PROJECT_FOLDER_1.name} - Requires", counts_folder_1)

    if counts_folder_2:
        output_ranking(f"{PROJECT_FOLDER_2.name} - Requires", counts_folder_2)

    output_ranking("Combined Requires:", total_counts)
