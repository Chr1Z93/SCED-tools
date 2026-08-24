import argparse
import json
from pathlib import Path


def escape_lua(code: str) -> str:
    """Escape Lua code as a JSON string."""
    return json.dumps(code, ensure_ascii=False)


def unescape_lua(code: str) -> str:
    """Unescape JSON-encoded Lua code."""
    return json.loads(code)


def main():
    parser = argparse.ArgumentParser(
        description="Escape or unescape JSON-encoded Lua code."
    )

    parser.add_argument("input", type=Path, help="Input file")
    parser.add_argument("output", type=Path, help="Output file")
    parser.add_argument(
        "mode",
        choices=["escape", "unescape"],
        help="Whether to escape or unescape the Lua code",
    )

    args = parser.parse_args()
    code = args.input.read_text(encoding="utf-8")

    if args.mode == "escape":
        result = escape_lua(code)
    else:
        result = unescape_lua(code)

    args.output.write_text(result, encoding="utf-8")


if __name__ == "__main__":
    main()
