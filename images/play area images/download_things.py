import asyncio
import random
import re
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
import click  # For the command-line interface
from colorama import Fore, Style
from lupa import LuaRuntime
from tqdm.asyncio import tqdm

# Constants
MAX_SIMULTANEOUS_DOWNLOADS = 20
REDUCED_MAX_SIMULTANEOUS_DOWNLOADS = 5  # For resume mode
RETRY_LIMIT = 3
TIMEOUT = 20  # seconds, doubled as per request
SUMMARY_FILE = "summary.txt"

# Output directory for images
output_dir = Path("Images Output")

def sanitize_filename(filename):
    # Replace disallowed characters with an underscore
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

# Function to clean up folder names
def clean_folder_name(name):
    name = re.sub(r"^\d{1,2}\-[A-Z]\s", "", name)
    if name.endswith(".com"):
        name = name[:-4]
    return name


async def download_image(image_data, session, resume_mode=False):
    name = image_data["Name"]
    url = image_data["URL"]
    # Parse the URL and extract the path without query parameters
    parsed_url = urlparse(url)
    file_extension = 'jpg' if parsed_url.path.endswith('/') else parsed_url.path.split('.')[-1]
    # Construct the valid file name
    campaign = clean_folder_name(image_data["Campaign"])
    scenario = clean_folder_name(image_data["Scenario"])
    # Use sanitized name for the filename
    sanitized_name = sanitize_filename(name)
    output_path = output_dir / campaign / scenario / f"{sanitized_name}.{file_extension}"


    # Make sure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    retries = 0
    while retries < RETRY_LIMIT:
        try:
            async with session.get(url, timeout=TIMEOUT) as response:
                if response.status == 200:
                    with open(output_path, "wb") as f, tqdm(
                        desc=name,
                        total=response.content_length,
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        leave=False,
                    ) as progress:
                        async for data in response.content.iter_chunked(1024):
                            f.write(data)
                            progress.update(len(data))
                    tqdm.write(f"{Fore.GREEN}Downloaded: {output_path}{Style.RESET_ALL}")
                    return {"status": "success", "name": name, "url": url}
                else:
                    tqdm.write(
                        f"{Fore.YELLOW}[Retry {retries + 1}/{RETRY_LIMIT}] Failed to download (status code {response.status}): {name}{Style.RESET_ALL}"
                    )
                    retries += 1
                    await asyncio.sleep(random.uniform(0.5, 2))
        except asyncio.TimeoutError:
            print(
                f"{Fore.YELLOW}[Retry {retries + 1}/{RETRY_LIMIT}] Timeout for {name}, retrying...{Style.RESET_ALL}"
            )
            retries += 1
            await asyncio.sleep(random.uniform(0.5, 2))
        except Exception as e:
            print(f"{Fore.RED}Error downloading {name}: {e}{Style.RESET_ALL}")
            return {"status": "error", "name": name, "url": url, "error": str(e)}
    print(
        f"{Fore.RED}Failed to download after {RETRY_LIMIT} retries: {name}{Style.RESET_ALL}"
    )
    return {"status": "fail", "name": name, "url": url}


async def download_images(images_data, resume_mode=False):
    max_simultaneous_downloads = (
        REDUCED_MAX_SIMULTANEOUS_DOWNLOADS
        if resume_mode
        else MAX_SIMULTANEOUS_DOWNLOADS
    )
    async with aiohttp.ClientSession() as session:
        tasks = []
        for image_data in images_data:
            await asyncio.sleep(random.uniform(0, 1))
            task = asyncio.create_task(download_image(image_data, session, resume_mode))
            tasks.append(task)
            if len(tasks) >= max_simultaneous_downloads:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results


def load_lua_file(file_path):
    lua = LuaRuntime(unpack_returned_tuples=True)
    with open(file_path) as file:
        lua.execute(file.read())
    lua_globals = lua.globals()
    return lua_globals["PLAYAREA_IMAGE_DATA"]


def save_summary(summary_data, path=output_dir / SUMMARY_FILE):
    with open(path, "w") as f:
        f.write(f"Success Count: {summary_data['success_count']}\n")
        f.write(f"Fail Count: {summary_data['fail_count']}\n")
        f.write(f"Total Files: {summary_data['total_count']}\n")
        f.write("Failed URLs:\n")
        for failed_image in summary_data.get("failed", []):
            f.write(f"{failed_image['url']}\n")


@click.command()
@click.option(
    "-r", "--resume", is_flag=True, help="Resume failed downloads from previous run or download any new images in the  table."
)
def main(resume):
    if resume:
        if not output_dir.exists():
            print(
                f"{Fore.RED}Resume mode activated but 'Images Output' not found.{Style.RESET_ALL}"
            )
            return

        # Load data and check for missing files
        lua_file_path = Path("PlayAreaImageData.ttslua")
        data = load_lua_file(lua_file_path)
        images_data = []  # Extract image data from Lua data
        for campaign, scenarios in data.items():
            for scenario, images in scenarios.items():
                for _image_num, image in images.items():
                    image["Campaign"] = campaign
                    image["Scenario"] = scenario
                    images_data.append(image)
        missing_images = [
            image
            for image in images_data
            if not (
                output_dir
                / clean_folder_name(image["Campaign"])
                / clean_folder_name(image["Scenario"])
                / f"{sanitize_filename(image['Name'])}.{'jpg' if urlparse(image['URL']).path.endswith('/') else urlparse(image['URL']).path.split('.')[-1]}"
            ).exists()
        ]
        if missing_images:
            print(
                f"Found {len(missing_images)} missing images. Attempting to download..."
            )
            results = asyncio.run(download_images(missing_images, resume_mode=True))
    else:
        if output_dir.exists():
            raise FileExistsError(
                f"{Fore.RED}The directory '{output_dir}' already exists. Exiting to prevent overwriting.{Style.RESET_ALL}"
            )
        output_dir.mkdir(parents=True)
        lua_file_path = Path("PlayAreaImageData.ttslua")
        data = load_lua_file(lua_file_path)
        images_data = []  # Extract image data from Lua data
        for campaign, scenarios in data.items():
            for scenario, images in scenarios.items():
                for _image_num, image in images.items():
                    image["Campaign"] = campaign
                    image["Scenario"] = scenario
                    images_data.append(image)
        results = asyncio.run(download_images(images_data))

    # Process results and save summary
    success_count = sum(
        1 for result in results if result and result.get("status") == "success"
    )
    fail_count = sum(
        1 for result in results if result and result.get("status") == "fail"
    )
    error_count = sum(
        1 for result in results if result and result.get("status") == "error"
    )
    total_count = len(images_data)
    failed_images = [
        result
        for result in results
        if result and result.get("status") in ["fail", "error"]
    ]
    summary_data = {
        "success_count": success_count,
        "fail_count": fail_count,
        "error_count": error_count,
        "total_count": total_count,
        "failed": failed_images,
    }
    save_summary(summary_data)
    print(
        f"{Fore.GREEN}Successfully downloaded {success_count} images.{Style.RESET_ALL}"
    )
    print(
        f"{Fore.RED}Failed to download {fail_count} images. Encountered {error_count} errors out of {total_count} total.{Style.RESET_ALL}"
    )


if __name__ == "__main__":
    main()
