import json
import os
import platform
import urllib.error
import urllib.request
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

GITHUB_API = "https://api.github.com/repos/Chr1Z93/SCED/releases/latest"
SCED_RAW_BASE = "https://raw.githubusercontent.com/Chr1Z93/SCED/main"

# The release asset starts with this prefix
SCED_ASSET_PREFIX = "Arkham"

# Image stored inside the SCED repository
SCED_IMAGE_FILENAME = "ArkhamSCE.png"

# Tabletop Simulator save location relative to the user's data directory
TTS_SUFFIX = Path("Tabletop Simulator") / "Saves"

PLATFORM = platform.system()

# ============================================================================
# Console output
# ============================================================================


def print_status(message: str) -> None:
    """Print a normal status message."""
    print(f"  {message}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"  [OK] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"  [ERROR] {message}")


# ============================================================================
# Path handling
# ============================================================================


def get_windows_documents_dir() -> Path:
    """
    Retrieve the user's Windows Documents directory.

    Windows allows users to move the Documents folder, so we check the
    registry instead of assuming it is located at %USERPROFILE%\\Documents.
    """
    try:
        import winreg

        registry_path = (
            r"Software\Microsoft\Windows\CurrentVersion" r"\Explorer\User Shell Folders"
        )

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
            # "Personal" is the registry value containing the Documents path
            documents_path, _ = winreg.QueryValueEx(key, "Personal")

        # Expand variables such as %USERPROFILE%
        return Path(os.path.expandvars(documents_path))

    except (OSError, ImportError):
        # If the registry lookup fails, fall back to the conventional path
        return Path.home() / "Documents"


def get_output_folder() -> Path:
    """
    Return the folder where Tabletop Simulator save files are stored.

    The location differs between Windows, macOS and Linux.
    """
    if PLATFORM == "Windows":
        base_dir = get_windows_documents_dir() / "My Games"

    elif PLATFORM == "Darwin":
        # macOS stores the relevant data below ~/Library
        base_dir = Path.home() / "Library"

    else:
        # Linux / other Unix-like systems
        base_dir = Path.home() / ".local" / "share"

    return base_dir / TTS_SUFFIX


def get_local_filename(asset_name: str) -> str:
    """
    Convert GitHub's asset filename to the filename used locally.

    GitHub release assets use dots where the local SCED filename uses spaces.
    Example:
        Arkham.SCE.1.2.3.json
        -> Arkham SCE 1.2.3.json
    """
    return asset_name.replace("Arkham.SCE.", "Arkham SCE ")


# ============================================================================
# GitHub
# ============================================================================


def get_latest_sced_asset() -> dict:
    """
    Query GitHub and return the SCED save asset from the latest release.

    Raises:
        RuntimeError: If no matching asset can be found.
        urllib.error.URLError: If GitHub cannot be reached.
        json.JSONDecodeError: If GitHub returns invalid JSON.
    """
    request = urllib.request.Request(
        GITHUB_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "SCED-Installer",
        },
    )

    with urllib.request.urlopen(request) as response:
        release = json.load(response)

    # Look through all release assets for the SCED save file.
    for asset in release.get("assets", []):
        if asset["name"].startswith(SCED_ASSET_PREFIX):
            return asset

    raise RuntimeError("Could not find the SCED save asset in the latest release.")


# ============================================================================
# Downloading
# ============================================================================


def download_file(url: str, output_file: Path) -> None:
    """
    Download a file and save it to output_file.

    A temporary file is used so an interrupted download does not leave
    behind a partially downloaded file with the final filename.
    """
    temp_file = output_file.with_suffix(output_file.suffix + ".tmp")

    try:
        print_status(f"Downloading: {output_file.name}")

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "SCED-Installer"},
        )

        with urllib.request.urlopen(request) as response:
            with open(temp_file, "wb") as file:
                file.write(response.read())

        # Only replace the final file once the download completed successfully
        temp_file.replace(output_file)

    except (urllib.error.URLError, OSError) as error:
        temp_file.unlink(missing_ok=True)
        raise RuntimeError(f"Download failed: {error}") from error


# ============================================================================
# Installation
# ============================================================================


def install_file(url: str, output_file: Path) -> bool:
    """
    Download a file if it does not already exist.

    Returns:
        True  if the file was downloaded.
        False if the file already existed.
    """
    if output_file.exists():
        print_status(f"Already exists: {output_file.name}")
        return False

    download_file(url, output_file)
    print_success(f"Installed: {output_file.name}")
    return True


def download_sced() -> None:
    """
    Download the latest SCED save file and its associated image.
    """
    print()
    print("=" * 60)
    print(" SCED Installer")
    print("=" * 60)
    print()

    # ------------------------------------------------------------------------
    # Determine installation directory
    # ------------------------------------------------------------------------

    output_folder = get_output_folder()

    print_status(f"Installation directory:")
    print_status(f"  {output_folder}")
    print()

    # Create the directory if it does not exist yet
    try:
        output_folder.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise RuntimeError(
            f"Could not create installation directory: {error}"
        ) from error

    # ------------------------------------------------------------------------
    # Find the latest SCED release
    # ------------------------------------------------------------------------

    print_status("Checking GitHub for the latest SCED release...")

    try:
        asset = get_latest_sced_asset()

    except (
        urllib.error.URLError,
        json.JSONDecodeError,
        RuntimeError,
    ) as error:
        print_error(f"Could not determine latest SCED release: {error}")
        return

    filename = get_local_filename(asset["name"])
    output_file = output_folder / filename

    print_success(f"Latest release: {filename}")
    print()

    # ------------------------------------------------------------------------
    # Download SCED save file
    # ------------------------------------------------------------------------

    try:
        install_file(
            asset["browser_download_url"],
            output_file,
        )
    except RuntimeError as error:
        print_error(str(error))
        return

    # ------------------------------------------------------------------------
    # Download associated image
    #
    # The image is stored in the repository rather than as a release asset.
    # Its filename is changed to match the downloaded JSON/save file.
    # ------------------------------------------------------------------------

    image_file = output_file.with_suffix(".png")
    image_url = f"{SCED_RAW_BASE}/.vscode/{SCED_IMAGE_FILENAME}"

    print()
    print_status("Checking SCED image...")

    try:
        install_file(image_url, image_file)
    except RuntimeError as error:
        print_error(str(error))
        return


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    try:
        download_sced()

    except Exception as error:
        # Catch unexpected errors
        print()
        print_error(f"Unexpected error: {error}")

    finally:
        # Keep the console open so the user can read the result.
        print()
        input("Press Enter to close...")
