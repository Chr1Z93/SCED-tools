import json


def validate_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("JSON syntax is valid!")
        return True
    except json.JSONDecodeError as e:
        print(f"JSON syntax is invalid at: {e}")
        return False
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return False


validate_json(r"C:\Users\christian.puls\Downloads\All Campaigns.json")
