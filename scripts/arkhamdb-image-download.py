import requests
import os
import mysql.connector
from mysql.connector import Error
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # type: ignore

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# MySQL connection details
db_config = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "symfony_user",
    "password": "symfony_password",
    "database": "symfony",
}

# Base URL
base_url = "https://arkhamdb.com/bundles/cards/"

# Directory to save images
save_dir = "card_images"


# Function to download image with retry logic
def download_image(url, file_name):
    try:
        # Configure session with retry strategy
        session = requests.Session()
        retries = Retry(
            total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))

        response = session.get(url, timeout=10)
        response.raise_for_status()
        with open(file_name, "wb") as file:
            file.write(response.content)
        logging.info(f"Downloaded: {file_name}")
        return True
    except requests.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
        return False


# Function to get card IDs from database
def get_card_ids():
    try:
        with mysql.connector.connect(**db_config) as connection:
            with connection.cursor() as cursor:
                query = "SELECT code FROM card"
                cursor.execute(query)
                return [row[0] for row in cursor.fetchall()]  # type: ignore
    except Error as e:
        logging.error(f"Error fetching card IDs: {e}")
        return []


def process_card_id(card_id):
    # Check if any of the expected image files exist
    for ext in [".png", ".jpg", ".jpeg"]:
        file_name = os.path.join(save_dir, f"{card_id}{ext}")
        if os.path.exists(file_name):
            logging.info(f"File already exists: {file_name}")
            return  # Skip downloading if the file exists

    # If no files exist, try downloading
    for ext in [".png", ".jpg", ".jpeg"]:
        url = base_url + card_id + ext
        file_name = os.path.join(save_dir, f"{card_id}{ext}")
        if download_image(url, file_name):
            break  # Move to next ID if download successful
    time.sleep(1)  # Add a delay to avoid overwhelming the server


# Main execution
os.makedirs(save_dir, exist_ok=True)

card_ids = get_card_ids()

with ThreadPoolExecutor(max_workers=5) as executor:
    executor.map(process_card_id, card_ids)

logging.info("Download complete!")
