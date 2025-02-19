import importlib
import os
import pkgutil
import time
import tempfile

from classes import CYCLES
from classes.CONSTANTS import Links

from selenium import webdriver
from dotenv import load_dotenv
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

    wait_element(
        ".flex.items-center.justify-center.fixed.z-50.bg-gray-200.h-screen.w-screen.inset-0.ng-tns-c98-0.ng-star-inserted"
    )
    print("✅ Page loaded!")

    time.sleep(1)


def fill_login_form():
    wait = WebDriverWait(driver, 10)
    login_input = find_element_by_css("input.flex.border.appearance-none.leading-tight")
    login_button = find_element_by_css(
        "button.flex.justify-center.items-center.cursor-pointer"
    )

    login_input.send_keys(EMAIL)  # type: ignore
    login_button.click()
    wait_element()

    time.sleep(1)
    password_input = find_element_by_css(
        "input.flex.border.appearance-none.leading-tight.w-full.pl-10.pr-4.pr-8.h-10.text-xs.border-gray-400.text-gray-800.rounded"
    )
    password_input.send_keys(PASSWORD)  # type: ignore
    time.sleep(1)
    login_button = find_element_by_css(
        "button.flex.justify-center.items-center.cursor-pointer"
    )
    login_button.click()
    wait_element()
    time.sleep(1)

    try:
        wait.until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    ".swal2-popup.swal2-modal.swal2-icon-question.swal2-show",
                )
            )
        )
        print("⚠️ Dispositivo já conectado!")
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
    wait_element(".ngt-shining-xs")
    print("✅ Conteúdo carregado!")
    time.sleep(1)


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
            print(
                f"❌ Erro: não foi possível encontrar ou clicar no ciclo com o texto '{cycle_text}'."
            )
            raise e

    def get_available_cycle():
        """
        Percorre todas as classes dentro de 'classes.CYCLES' e retorna a primeira com 'CAN_FILL = True'.
        """
        for _, module_name, _ in pkgutil.iter_modules(CYCLES.__path__):
            module = importlib.import_module(f"classes.CYCLES.{module_name}")

            class_name = module_name.replace("_", "")
            cycle_class = getattr(module, class_name, None)

            if (
                cycle_class
                and hasattr(cycle_class, "CAN_FILL")
                and hasattr(cycle_class, "NAME")
            ):
                if cycle_class.CAN_FILL:
                    print(f"✅ Ciclo selecionado: {cycle_class.NAME}")
                    return cycle_class.NAME

        print("❌ Nenhum ciclo disponível para preenchimento.")
        return None

    try:
        parent_xpath = (
            "(//div[contains(@class, 'float-right ml-2 ng-star-inserted')])[2]"
        )
        link_xpath = (
            f"{parent_xpath}//a[contains(@class, 'cursor-pointer ng-star-inserted')]"
        )

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

    cycle = get_available_cycle()
    select_cycle(cycle)
    time.sleep(1)

    wait_element(".block-page-div-loader")

    try:
        close_button_div = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//div[contains(@class, 'cursor-pointer z-50 absolute right-0 top-0 m-2 ng-star-inserted')]",
                )
            )
        )

        print("Clicando no botão de fechar...")
        close_button_div.click()
        time.sleep(1)

    except Exception as e:
        print(f"❌ Erro ao clicar no botão de fechar: {e}")
        raise e


def fill_form():
    print("✍️ Preenchendo o formulário...")


def close_pending_issues(tbody, rows):
    print("⚠️ There are pending issues! Starting the process to close them...")

    try:
        pending_row = None

        for row in rows:
            try:
                status_badge = row.find_element(
                    By.XPATH, ".//div[contains(text(),'Pendente')]"
                )
                status_text = status_badge.text.strip()
                if "PENDENTE" in status_text.upper():
                    pending_row = row
                    break
            except Exception:
                continue

        if pending_row is None:
            print("❌ Nenhuma linha pendente encontrada.")
            return

        truncate_element = pending_row.find_element(By.CSS_SELECTOR, ".truncate")
        print("✅ Linha pendente encontrada. Clicando na linha...")

        driver.execute_script("arguments[0].scrollIntoView(true);", truncate_element)
        time.sleep(1)

        truncate_element.click()
        wait_element(".block-page-div-loader")

        print("✅ Formulário carregado.")
        fill_form()

    except Exception as e:
        print("❌ Erro ao fechar as pendências:", e)
        raise e


def switch_page():
    print("✅ No pending issues found. Switching to the next page...")

    try:
        actions = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//ngt-action"))
        )

        if len(actions) < 2:
            print("Not enough pagination actions found.")
            return False

        penultimate_action = actions[-2]
        next_page_button = penultimate_action.find_element(By.TAG_NAME, "a")

        print("Switching to next page...")

        driver.execute_script("arguments[0].scrollIntoView(true);", next_page_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", next_page_button)
        time.sleep(1)
        return True
    except Exception as e:
        print("Error while switching page:", e)
        return False


def check_pgrs_pending():
    time.sleep(1)
    tbody = driver.find_element(By.CSS_SELECTOR, "tbody.bg-white")
    rows = tbody.find_elements(By.TAG_NAME, "tr")
    pending_count = 0
    non_pending_count = 0

    for row in rows:
        try:
            status_badge = row.find_element(
                By.XPATH, ".//div[contains(text(),'Pendente')]"
            )
            status_text = status_badge.text.strip()
            if "PENDENTE" in status_text.upper():
                pending_count += 1
            else:
                non_pending_count += 1
        except Exception as e:
            non_pending_count += 1

    print("Pending rows:", pending_count)
    print("Non-pending rows:", non_pending_count)
    return pending_count, tbody, rows


def navigate_pages_until_pending():
    """
    Navega pelas páginas até encontrar algum registro pendente.
    """
    while True:
        pending_count, tbody, rows = check_pgrs_pending()
        if pending_count > 0:
            close_pending_issues(tbody, rows)
            break
        else:
            success = switch_page()
            if not success:
                print("Could not switch page, exiting loop.")
                break
            wait_element(".block-page-div-loader")
            time.sleep(1)


def run_bot():
    print("🔹 Starting BOT_CEF...")
    url = Links.url
    try:
        access_page(url)
        fill_login_form()
        data_listing_page()
        data_page_filter()
        navigate_pages_until_pending()
    finally:
        driver.quit()
        print("✅ Bot finished!")


if __name__ == "__main__":
    run_bot()
