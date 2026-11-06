import argparse
import json
import os
import re

from pathlib import Path
from urllib.parse import unquote

import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# MARK: Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / ".env")
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "TTS-uploads").strip("/")
UPLOAD_CACHE = {}
REPORT = {
    "uploaded": [],
    "reused": [],
    "missing": [],
    "upload_errors": [],
    "json_errors": [],
    "processing_errors": [],
    "processed": [],
}

# ---------------------------------------------------------------------------
# MARK: Cloudinary
# ---------------------------------------------------------------------------


def initialize_cloudinary():
    """Initialize Cloudinary using environment variables."""

    required = (
        "CLOUDINARY_CLOUD_NAME",
        "CLOUDINARY_API_KEY",
        "CLOUDINARY_API_SECRET",
    )

    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(f"Missing Cloudinary credentials: {', '.join(missing)}")

    cloudinary.config(
        cloud_name=os.environ["CLOUDINARY_CLOUD_NAME"],
        api_key=os.environ["CLOUDINARY_API_KEY"],
        api_secret=os.environ["CLOUDINARY_API_SECRET"],
        secure=True,
    )


def get_public_id(filename, locale):
    """Generate a deterministic Cloudinary public ID."""

    name = Path(filename).stem
    name = re.sub(r"[^\w-]", "_", name)
    parts = [CLOUDINARY_FOLDER, locale, name]
    return "/".join(part for part in parts if part)


def upload_file(file_path, locale):
    """
    Upload a local file to Cloudinary.

    Existing assets with the same public ID are overwritten.
    Files already uploaded during this run reuse their URL.
    """

    file_path = Path(file_path).resolve()

    if not file_path.is_file():
        print(f"  [MISSING] {file_path}")
        REPORT["missing"].append(str(file_path))
        return None

    public_id = get_public_id(file_path.name, locale)

    if public_id in UPLOAD_CACHE:
        REPORT["reused"].append(str(file_path))
        return UPLOAD_CACHE[public_id]

    print(f"  Uploading: {file_path.name}")

    try:
        result = cloudinary.uploader.upload(
            str(file_path),
            public_id=public_id,
            overwrite=True,
            invalidate=True,
            unique_filename=False,
            use_filename=False,
            resource_type="auto",
        )

        url = result["secure_url"]

        UPLOAD_CACHE[public_id] = url
        REPORT["uploaded"].append(str(file_path))

        print(f"  [OK] {url}")

        return url

    except Exception as error:
        print(f"  [UPLOAD ERROR] {file_path}: {error}")

        REPORT["upload_errors"].append(
            {
                "file": str(file_path),
                "error": str(error),
            }
        )

        return None


# ---------------------------------------------------------------------------
# MARK: Local file paths
# ---------------------------------------------------------------------------


def resolve_local_path(value):
    """
    Convert a TTS file URI into a local filesystem path.

    Example:
        file:///C:\\git\\assets\\card.webp

    Also handles:
        file:///C:/git/assets/card.webp
        file://server/share/card.webp
    """

    if not isinstance(value, str):
        return None

    if not value.lower().startswith("file://"):
        return None

    path = unquote(value[7:])

    # Windows drive letter URI:
    # /C:/folder/file.webp -> C:\\folder\\file.webp
    if re.match(r"^/[a-zA-Z]:[/\\]", path):
        path = path[1:]

    if os.name == "nt":
        path = path.replace("/", "\\")

    return Path(path)


# ---------------------------------------------------------------------------
# MARK: JSON traversal
# ---------------------------------------------------------------------------


def process_value(value, locale):
    """Recursively process JSON data."""

    if isinstance(value, dict):
        for key, item in value.items():
            value[key] = process_value(item, locale)

        return value

    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = process_value(item, locale)

        return value

    if isinstance(value, str):
        local_path = resolve_local_path(value)

        if local_path is not None:
            url = upload_file(local_path, locale)

            if url is not None:
                return url

        return value

    return value


# ---------------------------------------------------------------------------
# MARK: JSON processing
# ---------------------------------------------------------------------------


def write_json(data, output_path):
    """Write JSON atomically to avoid corrupting files on interruption."""

    output_path = Path(output_path)
    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")

    temp_path.replace(output_path)


def process_json_file(file_path, locale, in_place=False):
    """Load, process and save one JSON file."""

    file_path = Path(file_path)

    print(f"\nProcessing: {file_path}")

    try:
        with file_path.open("r", encoding="utf-8-sig") as file:
            data = json.load(file)

    except Exception as error:
        print(f"[JSON ERROR] {file_path}: {error}")
        REPORT["json_errors"].append({"file": str(file_path), "error": str(error)})
        return

    try:
        data = process_value(data, locale)

        if in_place:
            output_path = file_path
        else:
            output_path = file_path.with_name(
                f"{file_path.stem}_cloudinary{file_path.suffix}"
            )

        write_json(data, output_path)
        REPORT["processed"].append(str(file_path))
        print(f"[OK] Saved: {output_path}")

    except Exception as error:
        print(f"[PROCESSING ERROR] {file_path}: {error}")
        REPORT["processing_errors"].append(
            {"file": str(file_path), "error": str(error)}
        )


# ---------------------------------------------------------------------------
# MARK: Reporting
# ---------------------------------------------------------------------------


def print_report():
    """Print a summary of the processing results."""

    print("\n" + "=" * 50)
    print("UPLOAD REPORT")
    print("=" * 50)

    print(f"JSON files processed:    {len(REPORT['processed'])}")
    print(f"Files uploaded:          {len(REPORT['uploaded'])}")
    print(f"Files reused:            {len(REPORT['reused'])}")
    print(f"Files not found:         {len(REPORT['missing'])}")
    print(f"Upload errors:           {len(REPORT['upload_errors'])}")
    print(f"JSON errors:             {len(REPORT['json_errors'])}")
    print(f"Processing errors:       {len(REPORT['processing_errors'])}")

    error_groups = (
        ("MISSING FILES", REPORT["missing"]),
        ("UPLOAD ERRORS", REPORT["upload_errors"]),
        ("JSON ERRORS", REPORT["json_errors"]),
        ("PROCESSING ERRORS", REPORT["processing_errors"]),
    )

    for title, entries in error_groups:
        if not entries:
            continue

        print(f"\n--- {title} ---")

        for entry in entries:
            if isinstance(entry, dict):
                print(f"File: {entry['file']}")
                print(f"Error: {entry['error']}")
            else:
                print(entry)

    print("\n" + "=" * 50)

    if any(
        REPORT[key]
        for key in (
            "missing",
            "upload_errors",
            "json_errors",
            "processing_errors",
        )
    ):
        print("Finished with issues.")
    else:
        print("Finished successfully.")

    print("=" * 50)


# ---------------------------------------------------------------------------
# MARK: Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Upload Tabletop Simulator assets to Cloudinary."
    )

    parser.add_argument(
        "path",
        type=Path,
        nargs="?",
        help="TTS JSON file or folder containing JSON files",
    )

    parser.add_argument(
        "--locale",
        help="Language locale for uploaded assets (e.g. en, de, fr)",
    )

    args = parser.parse_args()

    # Get path
    if args.path is None:
        user_input = input("Enter path to TTS JSON file or folder: ").strip()

        if not user_input:
            parser.error("No path provided.")

        target = Path(user_input.strip('"')).resolve()
    else:
        target = args.path.resolve()

    if not target.exists():
        parser.error(f"Path does not exist: {target}")

    # Get locale
    locale = args.locale

    if locale is None:
        locale = input("Enter locale (e.g. en, de, fr): ").strip()

    locale = locale.strip().lower()

    if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]+)*", locale):
        parser.error(f"Invalid locale: {locale}")

    initialize_cloudinary()

    if target.is_file():
        if target.suffix.lower() != ".json":
            parser.error("Input file must be a JSON file.")

        process_json_file(target, locale, in_place=False)

    elif target.is_dir():
        json_files = sorted(target.rglob("*.json"))

        if not json_files:
            print("No JSON files found.")
            return

        print(f"Found {len(json_files)} JSON files.")

        for file_path in json_files:
            process_json_file(file_path, locale, in_place=True)

    print_report()


if __name__ == "__main__":
    main()
