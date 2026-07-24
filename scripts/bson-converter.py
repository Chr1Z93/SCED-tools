import json
import sys
from pathlib import Path
import bson


def bson_to_json(input_file: Path, output_file: Path):
    print(f"Reading BSON: {input_file}")

    try:
        data = bson.decode(input_file.read_bytes())
    except Exception as e:
        print(f"Error reading BSON: {e}")
        sys.exit(1)

    print(f"Writing JSON: {output_file}")

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("Conversion successful.")


def json_to_bson(input_file: Path, output_file: Path):
    print(f"Reading JSON: {input_file}")

    try:
        with input_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        sys.exit(1)

    print(f"Writing BSON: {output_file}")

    try:
        output_file.write_bytes(bson.encode(data))
    except Exception as e:
        print(f"Error writing BSON: {e}")
        sys.exit(1)

    print("Conversion successful.")


def convert(input_path, output_path=None):
    input_file = Path(input_path)

    if not input_file.exists():
        print(f"Error: File not found:\n{input_file.resolve()}")
        sys.exit(1)

    suffix = input_file.suffix.lower()

    if suffix == ".bson":
        output_file = (
            Path(output_path) if output_path else input_file.with_suffix(".json")
        )
        bson_to_json(input_file, output_file)

    elif suffix == ".json":
        output_file = (
            Path(output_path) if output_path else input_file.with_suffix(".bson")
        )
        json_to_bson(input_file, output_file)

    else:
        print(f"Unsupported file type: '{suffix}'")
        print("Supported extensions are .json and .bson")
        sys.exit(1)


def pause():
    # Keeps the console open when run by double-clicking or drag & drop.
    if sys.stdin.isatty():
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print("Drag a .json or .bson file onto this script")
            print("or use the command line:")
            print("python bson_converter.py <input> [output]")
            pause()
            sys.exit(1)

        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None

        convert(input_file, output_file)

    except Exception as e:
        print(f"\nUnexpected error:\n{e}")
        pause()
        raise

    pause()
