import json
import os

def format_number(num, decimal_places):
    rounded = round(num, decimal_places)
    if rounded.is_integer():
        return int(rounded)
    return rounded


def round_to_multiple_of_15(num):
    return round(num / 15) * 15


def round_json(obj, parent_key=None):
    if isinstance(obj, dict):
        if parent_key == "pos":
            return {
                k: (format_number(v, 4) if isinstance(v, float) else v)
                for k, v in obj.items()
            }
        elif parent_key == "rot":
            return {
                k: (
                    round_to_multiple_of_15(v) % 360
                    if isinstance(v, (int, float))
                    else v
                )
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

    with open(file_path, "w") as f:
        json.dump(rounded_data, f, indent=2)

for path, subdirs, files in os.walk(r"C:\git\SCED-downloads\decomposed"):
    for file in files:
        file_path = os.path.join(path, file)
        file_root, file_ext = os.path.splitext(file)
        if file_ext == ".luascriptstate":
            process_file(file_path)
