import os
import re
import sys

folder = r"C:\git\SCED-downloads\decomposed"

lookup_dict = {}


def fix_encapsulated_guid(file_path):
    file_name_without_ext = remove_extension(os.path.basename(file_path))
    GUID = file_name_without_ext[-6:]
    falseGUID = GUID[:5]

    content_pattern = re.compile(rf"\.{re.escape(falseGUID)}\.")

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    new_content = content_pattern.sub(f".{GUID}.", content)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(new_content)
        print(f"Updated content: {file_path}")


def remove_extension(file_name):
    file_root, _ = os.path.splitext(file_name)
    return file_root


def process_file(file_path):
    content_pattern = re.compile(r'"([^"]*\.\w{5})"')

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    def replace_match(match):
        key = match.group(1)
        if key in lookup_dict:
            return f'"{lookup_dict[key]}"'
        return match.group(0)  # If no match in lookup_dict, return original string

    new_content = content_pattern.sub(replace_match, content)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(new_content)
        print(f"Updated content: {file_path}")


def add_to_library(file_path):
    file_name_without_ext = remove_extension(os.path.basename(file_path))
    lookup_dict[file_name_without_ext[:-1]] = file_name_without_ext


# First pass to get replacement strings
for path, subdirs, files in os.walk(folder):
    for file in files:
        file_path = os.path.join(path, file)
        add_to_library(file_path)

# Second pass to process files
for path, subdirs, files in os.walk(folder):
    for file in files:
        file_path = os.path.join(path, file)
        process_file(file_path)
