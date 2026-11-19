from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse, unquote
import argparse

import requests

MAX_WORKERS = 8
TIMEOUT = 30


def download_file(url: str, output_dir: Path) -> tuple[str, str]:
    """Download a single file and return its status."""

    filename = Path(unquote(urlparse(url).path)).name
    output_path = output_dir / filename

    if output_path.exists():
        return filename, "Skipped (already exists)"

    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()

        output_path.write_bytes(response.content)

        return filename, "Downloaded"

    except requests.RequestException as exc:
        return filename, f"Failed: {exc}"


def main():
    parser = argparse.ArgumentParser(description="Download files from a list of URLs.")
    parser.add_argument("input", type=Path, help="Text file containing URLs")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("downloads"),
        help="Output directory (default: downloads)",
    )
    args = parser.parse_args()

    if not args.input.is_file():
        parser.error(f"Input file not found: {args.input}")

    urls = list(
        dict.fromkeys(
            line.strip()
            for line in args.input.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
    )

    if not urls:
        print("No URLs found.")
        return

    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(urls)} unique URLs.")
    print(f"Downloading to: {args.output.resolve()}\n")

    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(download_file, url, args.output): url for url in urls
        }

        for future in as_completed(futures):
            filename, status = future.result()
            results.append(status)

            print(f"{status:<30} {filename}")

    downloaded = results.count("Downloaded")
    skipped = results.count("Skipped (already exists)")
    failed = len(results) - downloaded - skipped

    print("\n" + "-" * 50)
    print(f"Total:      {len(urls)}")
    print(f"Downloaded: {downloaded}")
    print(f"Skipped:    {skipped}")
    print(f"Failed:     {failed}")


if __name__ == "__main__":
    main()
