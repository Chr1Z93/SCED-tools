# Rounds the scriptstates (primarily for Memory Bags)

import json
import os

BASE_FOLDER = r"C:\git\SCED-downloads\decomposed"


def format_number(num, decimal_places):
    rounded = round(num, decimal_places)
    if rounded.is_integer():
        return int(rounded)
    return rounded


def format_angle(num):
    return round(num / 15) * 15 % 360


def round_json(obj, parent_key=None):
    if isinstance(obj, dict):
        if parent_key == "pos":
            return {
                k: (format_number(v, 4) if isinstance(v, float) else v)
                for k, v in obj.items()
            }
        elif parent_key == "rot":
            return {
                k: (format_angle(v) if isinstance(v, (int, float)) else v)
                for k, v in obj.items()
            }
        else:
            return {k: round_json(v, k) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [round_json(elem, parent_key) for elem in obj]
    elif isinstance(obj, float):
        return format_number(obj, 4)
    else:
        return obj


def process_file(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    rounded_data = round_json(data)

    if rounded_data == data:
        return

    with open(file_path, "w") as f:
        json.dump(rounded_data, f, indent=2)


def round_scriptstates():
    for path, _, files in os.walk(BASE_FOLDER):
        for file in files:
            file_path = os.path.join(path, file)
            _, file_ext = os.path.splitext(file)
            if file_ext == ".luascriptstate":
                process_file(file_path)


if __name__ == "__main__":
    round_scriptstates()
