import os
import time
import random
import tempfile
import importlib

from classes import CYCLES
from classes.CONSTANTS import Links

from selenium import webdriver
from dotenv import load_dotenv
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from classes.CYCLES.SP_CAPITAL.SP_CAPITAL import ResponsesSPCAPITAL


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

def waitFunc():
    return WebDriverWait(driver, 30)


def wait_element(css_selector=".div-loader.h-16.w-16.ng-tns-c303-1"):
    wait = waitFunc()

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
    wait = waitFunc()
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
        print("⚠️  Dispositivo já conectado!")
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

LAST_CYCLE = None

def get_available_cycle(skip_cycle=None):
    """
    Percorre todas as pastas dentro de 'classes/CYCLES' e retorna o nome do primeiro ciclo com 'CAN_FILL = True',
    ignorando o ciclo passado em `skip_cycle`.
    """
    global LAST_CYCLE

    cycles_path = CYCLES.__path__[0]

    for cycle_folder in os.listdir(cycles_path):
        folder_path = os.path.join(cycles_path, cycle_folder)
        if os.path.isdir(folder_path):
            cycle_file = os.path.join(folder_path, f"{cycle_folder}.py")
            if os.path.exists(cycle_file):
                spec = importlib.util.spec_from_file_location(cycle_folder, cycle_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                class_name = cycle_folder.replace("_", "").upper()
                cycle_class = getattr(module, class_name, None)
                
                if cycle_class and hasattr(cycle_class, "CAN_FILL") and cycle_class.CAN_FILL:
                    cycle_name = cycle_class.NAME
                    if skip_cycle and cycle_name == skip_cycle:
                        continue  # Pular o último ciclo processado
                    
                    LAST_CYCLE = cycle_name
                    print(f"✅ Ciclo selecionado: {cycle_name}")
                    return cycle_name

    print("❌ Nenhum ciclo disponível para preenchimento.")
    return None


def select_cycle(cycle_text):
    """
    Seleciona o ciclo disponível na UI do site, dado o nome retornado por get_available_cycle().
    """
    wait = waitFunc()
    xpath = f"//div[contains(@class, 'scrollable-content')]//div[contains(normalize-space(.), '{cycle_text}')]"

    try:
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        print(f"✅ Ciclo encontrado: {element.text}")
        element.click()
    except Exception as e:
        print(f"❌ Erro: não foi possível encontrar ou clicar no ciclo '{cycle_text}'.")
        raise e


def filter_pending_reports():
    """
    Filtra os relatórios pendentes e executa a navegação até encontrar pendências ou acabar os ciclos.
    """
    global LAST_CYCLE

    wait = waitFunc()

    try:
        parent_xpath = "(//div[contains(@class, 'float-right ml-2 ng-star-inserted')])[2]"
        link_xpath = f"{parent_xpath}//a[contains(@class, 'cursor-pointer ng-star-inserted')]"

        filter_button = wait.until(EC.element_to_be_clickable((By.XPATH, link_xpath)))
        print("✅ Link encontrado.")
        filter_button.click()
        print("✅ Clicado no link encontrado.")
    except Exception as e:
        print("❌ Erro: Não foi possível encontrar ou clicar no link.")
        raise e

    time.sleep(2)

    try:
        print("Procurando: ng-arrow-wrapper")
        xpath = "(//ng-select[contains(@class, 'ng-select')])[last()]//span[contains(@class, 'ng-arrow-wrapper')]"
        find_city = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        print("✅ Elemento .ng-arrow-wrapper encontrado e clicável. Clicando...")
        find_city.click()
    except Exception as e:
        print(f"❌ Erro ao clicar no elemento: {e}")
        raise e

    wait_element(".block-page-div-loader")

    while True:
        cycle = get_available_cycle(skip_cycle=LAST_CYCLE)
        if not cycle:
            print("🚫 Nenhum novo ciclo disponível. Finalizando execução.")
            return

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
            print("🔹 Clicando no botão de fechar...")
            close_button_div.click()
            time.sleep(1)

            filter_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@title='Filtrar por: Pendentes e Vencidas']")
                )
            )
            print("🔹 Clicando no botão de filtro 'Filtrar por: Pendentes e Vencidas'...")
            filter_button.click()
            wait_element(".block-page-div-loader")
            time.sleep(1)

        except Exception as e:
            print(f"❌ Erro ao clicar em um dos botões: {e}")
            raise e

        has_pending_issues = navigate_pages_until_pending(cycle)

        if has_pending_issues is None:
            print(f"❌ Erro ao verificar pendências no ciclo '{cycle}'. Tentando novamente...")
            continue

        if has_pending_issues:
            print(f"⚠️  O ciclo '{cycle}' tem pendências. Processando...")
            break
        else:
            print(f"✅ O ciclo '{cycle}' não tem pendências. Buscando próximo ciclo...")
            LAST_CYCLE = cycle


def generate_random_date():
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_date = start_date + timedelta(days=random_days)
    return random_date.strftime('%d/%m/%Y')

def fill_form():
    print("✍️ Preenchendo o formulário...")
    wait_element(".ngt-shining-xs")
    
    def click_input_field(index, tab=False):
        input_fields = driver.find_elements(By.CSS_SELECTOR, "div.ng-input > input")
        if input_fields:
            driver.execute_script("arguments[0].scrollIntoView(true);", input_fields[index])
            time.sleep(0.5)
            input_fields[index].click()
            time.sleep(0.5)
            input_fields[index].send_keys(Keys.ENTER)
            if tab:
                return input_fields[index]
            time.sleep(0.5)
    
    time.sleep(1)
    click_input_field(0)
    time.sleep(1)
    
    print("Campo 1")
    input_field = click_input_field(1, tab=True)
    input_field.send_keys(Keys.TAB)
    time.sleep(1)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.ESTRUTURA_ARMAZENAMENTO)
    time.sleep(1)
    
    print("Campo 2")
    input_field = click_input_field(2, tab=True)
    input_field.send_keys(Keys.TAB)
    time.sleep(1)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.RESIDUOS_ENCAMINHADOS)
    time.sleep(1)
    
    print("Campo 3")
    input_field = click_input_field(3, tab=True)
    input_field.send_keys(Keys.TAB)
    time.sleep(1)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.EMPRESA_RESPONSAVEL)
    time.sleep(1)
    
    active_field.send_keys(Keys.TAB)
    time.sleep(1)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.ENDERECO_LOCAL)
    time.sleep(1)
    
    active_field.send_keys(Keys.TAB)
    time.sleep(1)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.RESIDUOS_ARMAZENADOS)
    time.sleep(1)
    
    # Upload de imagens (4 arquivos)
    photos_dir = os.path.join("classes", "CYCLES", "SP_CAPITAL", "PHOTOS")
    photo_files = [os.path.abspath(os.path.join(photos_dir, f"{i}.png")) for i in range(1, 5)]
    
    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    if len(file_inputs) >= 4:
        for file_input, photo_path in zip(file_inputs, photo_files):
            if os.path.exists(photo_path):
                file_input.send_keys(photo_path)
                print(f"📸 Upload de '{photo_path}' concluído.")
                time.sleep(.5)
            else:
                print(f"❌ Arquivo não encontrado: {photo_path}")
    else:
        print("❌ Não foram encontrados 4 campos de upload de arquivo.")
    
    print("Campo 4")
    input_field = click_input_field(4, tab=True)
    time.sleep(1)
    print("Campo 5")
    input_field = click_input_field(5, tab=True)
    input_field.send_keys(Keys.TAB)
    time.sleep(1)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.SUGESTAO_MELHORIA)
    time.sleep(1)
    
    print("Campo 6")
    input_field = click_input_field(6, tab=True)
    time.sleep(1)
    
    # Clicar no checkbox relativo ao elemento que contém "Lâmpadas"
    lampadas_checkbox = driver.find_element(
        By.XPATH, 
        "//span[contains(text(), 'Lâmpadas')]/ancestor::div[contains(@class, 'w-full flex gap-1')]/div[1]//div[contains(@style, 'padding: 1px') and contains(@class, 'border')]"
    )
    lampadas_checkbox.click()
    
    # print("Campo 7")
    # click_input_field(10)
    # time.sleep(.5)
    # print("input clicado")
    
    # wait = wait = waitFunc()
    # wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.w-full.truncate.font-semibold")))
    
    # more_option = find_element_by_css("span.w-full.truncate.font-semibold")
    # more_option.click()
    # time.sleep(2)
    # print("more option clicado")
    
    # click_away = find_element_by_css(".fill-current.self-center.text-lg.text-base-500.cursor-pointer")
    # click_away.click()
    # print("click fora")

    # click_input_field(10)
    # time.sleep(2)
    # active_field = driver.switch_to.active_element
    # active_field.send_keys(ResponsesSPCAPITAL.TRATAMENTO)
    # time.sleep(1)
    # active_field.send_keys(Keys.ENTER)
    
    wait_element(".block-page-div-loader")
    option = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//p[contains(text(), 'Sistema de logística reversa formalmente instituído')]"))
    )
    option.click()
    print("'Sistema de logística reversa formalmente instituído' clicado.")
    time.sleep(1)
    
    # 2. Aguarde que a opção "Mais Opções..." esteja visível e clique nela
    more_options = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, "//span[contains(text(), 'Mais Opções')]"))
    )
    more_options.click()
    print("'Mais Opções...' clicado.")
    time.sleep(1)

    # 3. Clicar fora do input para desfocar (por exemplo, clicando no body)
    driver.find_element(By.TAG_NAME, "body").click()
    print("Clique fora do input realizado.")
    time.sleep(1)

    # 4. Clicar novamente no input
    option = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//p[contains(text(), 'Sistema de logística reversa formalmente instituído')]"))
    )
    option.click()
    print("Input clicado novamente.")
    time.sleep(1)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.TRATAMENTO)

    print("✅ Todos os campos preenchidos com sucesso!")
    time.sleep(120)

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

    print("Com pendência:", pending_count)
    print("Sem pendência:", non_pending_count)
    return pending_count, tbody, rows


def navigate_pages_until_pending(cycle):
    try:
        while True:
            pending_count, tbody, rows = check_pgrs_pending()
            if pending_count > 0:
                close_pending_issues(tbody, rows)
                return True  
            else:
                print(f"✅ Não há pendências para o ciclo '{cycle}'.")
                return False  
    except Exception as e:
        print(f"❌ Erro ao navegar pelo ciclo '{cycle}': {e}")
        return None
        


def run_bot():
    print("🔹 Starting BOT_CEF...")
    url = Links.url
    try:
        access_page(url)
        fill_login_form()
        data_listing_page()
        filter_pending_reports()
    finally:
        driver.quit()
        print("✅ Bot finished!")


if __name__ == "__main__":
    run_bot()
