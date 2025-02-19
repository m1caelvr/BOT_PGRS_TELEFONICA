import os
import time
import tempfile

from selenium import webdriver
from dotenv import load_dotenv
from classes.CONSTANTS import Links
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

if os.getenv("GITHUB_ACTIONS") is None:
    load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def init_driver():
    temp_user_data_dir = tempfile.mkdtemp()
    download_dir = os.path.join(os.getcwd(), "downloads")

    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    chrome_options = Options()
    # chrome_options.add_argument("--headless")
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

driver = init_driver()
        
def wait_element(css_selector=".div-loader.h-16.w-16.ng-tns-c303-1", timeout=30):
    wait = WebDriverWait(driver, timeout)
    
    try:
        print("Esperando elemento aparacer...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        print("Elemento apareceu!")
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        print("✅ Elemento sumiu!")
    
    except Exception as e:
        print(f"❌ Timeout esperando o elemento {css_selector}: {e}")
        driver.quit()
        exit()

def find_element_by_css(css_selector):
    return driver.find_element(By.CSS_SELECTOR, css_selector)

def access_page(url):
    driver.get(url)
    print(f"🔹 Accessing page: {url}")

    title = driver.title
    print(f"📄 Page title: {title}")
    
    wait_element(".flex.items-center.justify-center.fixed.z-50.bg-gray-200.h-screen.w-screen.inset-0.ng-tns-c98-0.ng-star-inserted")
    print("✅ Page loaded!")
    
    time.sleep(1)

def fill_login_form():
    wait = WebDriverWait(driver, 10)
    login_input = find_element_by_css("input.flex.border.appearance-none.leading-tight")
    login_button = find_element_by_css("button.flex.justify-center.items-center.cursor-pointer")
    
    login_input.send_keys(EMAIL)
    login_button.click()
    wait_element()
    
    time.sleep(1)
    password_input = find_element_by_css("input.flex.border.appearance-none.leading-tight.w-full.pl-10.pr-4.pr-8.h-10.text-xs.border-gray-400.text-gray-800.rounded")
    password_input.send_keys(PASSWORD)
    time.sleep(1)
    login_button = find_element_by_css("button.flex.justify-center.items-center.cursor-pointer")
    login_button.click()
    wait_element()
    time.sleep(1)
    
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".swal2-popup.swal2-modal.swal2-icon-question.swal2-show")))
        print("❌ Dispositivo já conectado!")
        confirm_button = find_element_by_css("button.swal2-confirm.swal2-styled")
        confirm_button.click()
        time.sleep(1)
        wait_element()
    except:
        print("✅ Não há dispositivos conectados!")
        time.sleep(1)
        wait_element()
        driver.quit()
        exit()
        
def data_listing_page():
    time.sleep(1)
    wait_element(".block-page-div-loader")
    print("✅ Page loaded!")
    time.sleep(1)
    wait_element(".block-page-div-loader")
    time.sleep(1)
    print("✅ Data loaded!")
    time.sleep(3)
    
def data_page_filter():
    wait = WebDriverWait(driver, 30)
    
    def select_cycle(cycle_text):
        """
        Procura e clica no ciclo desejado dentro do container com classe 'scrollable-content'.
        Aceita parte do texto, por exemplo, "SÃO PAULO CAPITAL" encontra "SÃO PAULO CAPITAL 2024".
        
        :param cycle_text: Texto (ou parte) que identifica o ciclo.
        :param timeout: Tempo máximo para aguardar o elemento (em segundos).
        """
        xpath = f"//div[contains(@class, 'scrollable-content')]//div[contains(normalize-space(.), '{cycle_text}')]"
        
        try:
            element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            print(f"✅ Ciclo encontrado: {element.text}")
            element.click()
        except Exception as e:
            print(f"❌ Erro: não foi possível encontrar ou clicar no ciclo com o texto '{cycle_text}'.")
            raise e

    try:
        parent_xpath = "(//div[contains(@class, 'float-right ml-2 ng-star-inserted')])[2]"
        link_xpath = f"{parent_xpath}//a[contains(@class, 'cursor-pointer ng-star-inserted')]"
        
        filter_button = wait.until(EC.element_to_be_clickable((By.XPATH, link_xpath)))
        print(f"✅ Link encontrado.")
        filter_button.click()
        print(f"✅ Clicado no link encontrado.")
    except Exception as e:
        print("❌ Erro: Não foi possível encontrar ou clicar no link.")
        raise e
    
    time.sleep(2)
    
    try:
        print("procurando: ng-arrow-wrapper")
        xpath = "(//ng-select[contains(@class, 'ng-select')])[last()]//span[contains(@class, 'ng-arrow-wrapper')]"
        find_city = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        print("✅ Elemento .ng-arrow-wrapper encontrado e clicável. Clicando...")
        find_city.click()
    except Exception as e:
        print(f"❌ Erro ao clicar no elemento: {e}")
        raise e
        
    wait_element(".block-page-div-loader")
    select_cycle("SÃO PAULO CAPITAL")
    wait_element(".block-page-div-loader")
    
    try:        
        close_button_div = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'cursor-pointer z-50 absolute right-0 top-0 m-2 ng-star-inserted')]")))
        
        print("Clicando no botão de fechar...")
        close_button_div.click()
        
        time.sleep(10)  
    except Exception as e:
        print(f"❌ Erro ao clicar no botão de fechar: {e}")
        raise e
    

def run_bot():
    print("🔹 Starting BOT_CEF...")
    url = Links.url
    try:
        access_page(url)
        fill_login_form()
        data_listing_page()
        data_page_filter()
    finally:
        driver.quit()
        print("✅ Bot finished!")


if __name__ == "__main__":
    run_bot()
