import os
import time
import tempfile
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from classes.CONSTANTS import Links

if os.getenv("GITHUB_ACTIONS") is None:
    load_dotenv()

LOGIN = os.getenv("LOGIN")
PASSWORD = os.getenv("SENHA")


def init_driver():
    temp_user_data_dir = tempfile.mkdtemp()
    download_dir = os.path.join(os.getcwd(), "downloads")

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"user-data-dir={temp_user_data_dir}")

    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "plugins.always_open_pdf_externally": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def access_page(driver, url):
    driver.get(url)
    print(f"🔹 Accessing page: {url}")

    title = driver.title
    print(f"📄 Page title: {title}")
    time.sleep(5)


def run_bot():
    print("🔹 Starting BOT_CEF...")
    driver = init_driver()
    url = Links.url
    try:
        access_page(driver, url)
    finally:
        driver.quit()
        print("✅ Bot finished!")


if __name__ == "__main__":
    run_bot()
