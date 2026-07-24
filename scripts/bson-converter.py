import json
import sys
from pathlib import Path
import bson


def bson_to_json(input_path, output_path=None):
    input_file = Path(input_path)

    if not input_file.exists():
        print(f"Error: Could not find input file '{input_file.resolve()}'.")
        sys.exit(1)

    # Set default output file name if none provided (e.g., CloudInfo.bson -> CloudInfo.json)
    if output_path is None:
        output_file = input_file.with_suffix(".json")
    else:
        output_file = Path(output_path)

    print(f"Reading {input_file}...")
    try:
        raw_bytes = input_file.read_bytes()
        data = bson.decode(raw_bytes)
    except Exception as e:
        print(f"Error reading/decoding BSON data: {e}")
        sys.exit(1)

    print(f"Writing to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Done!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bson-converter.py <path_to_bson_file> [output_json_path]")
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None

    bson_to_json(in_file, out_file)
