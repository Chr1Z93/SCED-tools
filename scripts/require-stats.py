# Collects data about the number of required files

import os
import re
import json
from collections import defaultdict
from pathlib import Path

# Configuration: Path to your Tabletop Simulator project folders
PROJECT_FOLDER_1 = Path(r"C:\git\SCED")
PROJECT_FOLDER_2 = Path(r"C:\git\SCED-downloads")


def analyze_requires(base_folder):
    counts = defaultdict(int)
    # Combined regex for Lua/TTSLua files and JSON files
    # For Lua: require("path")
    # For JSON: "LuaScript": "require(\"path\")" - requires handling of escaped quotes
    require_pattern = re.compile(r'require\("([^"]+)"\)')

    if not os.path.isdir(base_folder):
        print(f"Error: Folder not found, skipping: {base_folder}")
        return counts

    try:
        for root, dirs, files in os.walk(base_folder):
            if ".git" in dirs:
                dirs.remove(".git")

            if ".vscode" in dirs:
                dirs.remove(".vscode")

            for file_name in files:
                if not file_name.endswith((".lua", ".ttslua", ".json")):
                    continue

                file_path = Path(root) / file_name

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    if file_name.endswith((".lua", ".ttslua")):
                        matches = require_pattern.findall(content)
                        for required_path in matches:
                            counts[required_path] += 1

                    elif file_name.endswith(".json"):
                        try:
                            data = json.loads(content)
                        except json.JSONDecodeError:
                            print(f"Warning: Skipping malformed JSON file: {file_path}")
                            continue

                        if isinstance(data, dict):
                            lua_script = data.get("LuaScript", "")
                            match = require_pattern.match(lua_script)
                            if match:
                                counts[match.group(1)] += 1
                        elif isinstance(data, list):
                            for obj in data:
                                if isinstance(obj, dict):
                                    lua_script = obj.get("LuaScript", "")
                                    match = require_pattern.match(lua_script)
                                    if match:
                                        counts[match.group(1)] += 1

                except PermissionError:
                    print(f"Warning: No permission to read file, skipping: {file_path}")
                except FileNotFoundError:
                    print(
                        f"Warning: File not found (e.g. broken symlink), skipping: {file_path}"
                    )
                except OSError as e:
                    print(f"Warning: OS error reading file {file_path}: {e}")
                except Exception as e:
                    print(f"Warning: Unexpected error processing file {file_path}: {e}")

    except OSError as e:
        print(f"Error: Cannot walk directory {base_folder}: {e}")

    return counts


def output_ranking(title, counts):
    # Sort the combined results
    ranking = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    print(f"\n{title}")
    print("----------------------")

    for file_path, count in ranking:
        if count > 99:
            print(f"{count} - {file_path}")
        elif count > 9:
            print(f" {count} - {file_path}")
        elif count > 4:
            print(f"  {count} - {file_path}")


if __name__ == "__main__":
    total_counts = defaultdict(int)

    # Analyze Project Folder 1
    print(f"Scanning '{PROJECT_FOLDER_1}' for requires...")
    counts_folder_1 = analyze_requires(PROJECT_FOLDER_1)
    for path, count in counts_folder_1.items():
        total_counts[path] += count

    # Analyze Project Folder 2
    print(f"Scanning '{PROJECT_FOLDER_2}' for requires...\n")
    counts_folder_2 = analyze_requires(PROJECT_FOLDER_2)
    for path, count in counts_folder_2.items():
        total_counts[path] += count

    if not total_counts:
        print("No 'require' statements found in either specified folder.")
        exit()

    print("Info: Ranking excludes files that only occur less than 5 times.")

    if counts_folder_1:
        output_ranking(f"{PROJECT_FOLDER_1.name} - Requires", counts_folder_1)

    if counts_folder_2:
        output_ranking(f"{PROJECT_FOLDER_2.name} - Requires", counts_folder_2)

    output_ranking("Combined Requires:", total_counts)
