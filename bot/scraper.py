import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import random
import tempfile
import importlib

from classes import CYCLES
from classes.CONSTANTS import Links

from zoneinfo import ZoneInfo
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
from AUTHORIZATION import check_status


if os.getenv("GITHUB_ACTIONS") is None:
    load_dotenv()


def init_driver():
    download_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(download_dir, exist_ok=True)

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    if not os.getenv("GITHUB_ACTIONS"):
        temp_user_data_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"user-data-dir={temp_user_data_dir}")
    else:
        chrome_options.add_argument("--headless")

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
    driver.set_window_size(1051, 846)
    return driver


EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

LAST_CYCLE = None

driver = init_driver()

def waitFunc(timeWait=30):
    return WebDriverWait(driver, timeWait)


def wait_element(css_selector=".div-loader.h-16.w-16.ng-tns-c303-1", timeWait=30):
    wait = waitFunc(timeWait)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, css_selector)))
    except Exception as e:
        time.sleep(2)


def find_element_by_css(css_selector):
    return driver.find_element(By.CSS_SELECTOR, css_selector)


def verify_hour():
    now = datetime.now(ZoneInfo("America/Sao_Paulo"))
    start = now.replace(hour=7, minute=30, second=0, microsecond=0)
    end = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if start < now < end:
        print("Horário entre 7:30 e 9:00 detectado. Encerrando a execução do script.")
        exit(0)


def access_page(url):
    driver.get(url)
    print(f"🔹 Accessing page: {url}")
    print(f"📄 Page title: {driver.title}")
    wait_element(".flex.items-center.justify-center.fixed.z-50.bg-gray-200.h-screen.w-screen.inset-0.ng-tns-c98-0.ng-star-inserted")
    print("✅ Page loaded!")
    time.sleep(1)


def fill_login_form():
    wait = waitFunc()
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
        print("⚠️  Dispositivo já conectado!")
        confirm_button = find_element_by_css("button.swal2-confirm.swal2-styled")
        confirm_button.click()
        time.sleep(1)
        wait_element()
    except Exception:
        print("✅ Não há dispositivos conectados!")
        time.sleep(1)
        wait_element()


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


def get_available_cycle(skip_cycle=None):
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
                        continue
                    LAST_CYCLE = cycle_name
                    print(f"✅ Ciclo selecionado: {cycle_name}")
                    return cycle_name
    print("❌ Nenhum ciclo disponível para preenchimento.")
    return None


def select_cycle(cycle_text):
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

    try:
        wait_element(".block-page-div-loader", timeWait=10)
    except Exception:
        pass

    while True:
        cycle = get_available_cycle(skip_cycle=LAST_CYCLE)
        if not cycle:
            print("🚫 Nenhum novo ciclo disponível. Finalizando execução.")
            return
        select_cycle(cycle)
        time.sleep(1)
        wait_element(".block-page-div-loader")
        try:
            close_button_div = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'cursor-pointer z-50 absolute right-0 top-0 m-2 ng-star-inserted')]")
            ))
            print("🔹 Clicando no botão de fechar...")
            close_button_div.click()
            time.sleep(1)
            filter_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@title='Filtrar por: Pendentes e Vencidas']")
            ))
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


def fill_form(cycle):
    print("Passo 1: Iniciando preenchimento do formulário")
    wait_element(".ngt-shining-xs")
    wait = waitFunc()

    def click_input_field(index, tab=False):
        input_fields = driver.find_elements(By.CSS_SELECTOR, "div.ng-input > input")
        if input_fields and index < len(input_fields):
            driver.execute_script("arguments[0].scrollIntoView(true);", input_fields[index])
            time.sleep(0.5)
            input_fields[index].click()
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-xs.w-full")))
            input_fields[index].send_keys(Keys.ENTER)
            if tab:
                return input_fields[index]
            time.sleep(0.5)

    click_input_field(0)

    print("Passo 2: Preenchendo a data")
    date_input = WebDriverWait(driver, 200).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'input.ng2-flatpickr-input.flatpickr-input'))
    )
    date = generate_random_date()
    date_input.send_keys(date)
    time.sleep(1)

    print("Passo 3: Preenchendo ESTRUTURA_ARMAZENAMENTO")
    input_field = click_input_field(1, tab=True)
    input_field.send_keys(Keys.TAB)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.ESTRUTURA_ARMAZENAMENTO)
    time.sleep(1)

    print("Passo 4: Preenchendo RESIDUOS_ENCAMINHADOS")
    input_field = click_input_field(2, tab=True)
    input_field.send_keys(Keys.TAB)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.RESIDUOS_ENCAMINHADOS)

    print("Passo 5: Preenchendo EMPRESA_RESPONSAVEL, ENDERECO_LOCAL e RESIDUOS_ARMAZENADOS")
    input_field = click_input_field(3, tab=True)
    input_field.send_keys(Keys.TAB)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.EMPRESA_RESPONSAVEL)
    active_field.send_keys(Keys.TAB)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.ENDERECO_LOCAL)
    active_field.send_keys(Keys.TAB)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.RESIDUOS_ARMAZENADOS)

    print("Passo 6: Realizando upload de imagens")
    photos_dir = os.path.join("classes", "CYCLES", "SP_CAPITAL", "PHOTOS")
    photo_files = [os.path.abspath(os.path.join(photos_dir, f"{i}.png")) for i in range(1, 5)]
    file_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
    if len(file_inputs) >= 4:
        for file_input, photo_path in zip(file_inputs[1:], photo_files):
            if os.path.exists(photo_path):
                file_input.send_keys(photo_path)
                time.sleep(0.5)
            else:
                print(f"❌ Arquivo não encontrado: {photo_path}")
    else:
        print("❌ Não foram encontrados 4 campos de upload de arquivo.")

    print("Passo 7: Avançando para os próximos campos")
    click_input_field(4, tab=True)
    input_field = click_input_field(5, tab=True)
    input_field.send_keys(Keys.TAB)
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.SUGESTAO_MELHORIA)
    click_input_field(6, tab=True)
    time.sleep(1)

    print("Passo 8: Selecionando opção 'Lâmpadas'")
    lampadas_checkbox = driver.find_element(
        By.XPATH, 
        "//span[contains(text(), 'Lâmpadas')]/ancestor::div[contains(@class, 'w-full flex gap-1')]/div[1]//div[contains(@style, 'padding: 1px') and contains(@class, 'border')]"
    )
    lampadas_checkbox.click()
    wait_element(".block-page-div-loader")

    print("Passo 9: Interagindo com dropdown de logística reversa")
    container = driver.find_element(
        By.XPATH, 
        "//div[contains(@class, 'ng-select-container') and descendant::p[@class='w-full' and normalize-space(text())='Sistema de logística reversa formalmente instituído']]"
    )
    container.click()
    time.sleep(1)

    print("Passo 10: Clicando em 'Mais Opções...'")
    mais_opcoes = driver.find_element(
        By.XPATH, 
        "//span[normalize-space(text())='Mais Opções...']"
    )
    mais_opcoes.click()
    time.sleep(1)

    print("Passo 11: Aguardando loader após 'Mais Opções...'")
    wait_element(".block-page-div-loader")
    time.sleep(1)

    print("Passo 12: Fechando dropdown")
    body = driver.find_element(By.TAG_NAME, "body")
    body.click()

    print("Passo 13: Reabrindo dropdown de logística reversa")
    container = driver.find_element(
        By.XPATH, 
        "//div[contains(@class, 'ng-select-container') and descendant::p[@class='w-full' and normalize-space(text())='Sistema de logística reversa formalmente instituído']]"
    )
    container.click()
    wait_element(".block-page-div-loader")

    print("Passo 14: Inserindo TRATAMENTO")
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.TRATAMENTO)

    print("Passo 15: Confirmando seleção")
    wait_element(".block-page-div-loader")
    active_field.send_keys(Keys.ENTER)
    time.sleep(0.5)
    wait_element(".block-page-div-loader")
    time.sleep(0.5)

    print("Passo 16: Adicionando justificativa")
    btn_justificativa = find_element_by_css(".flex.h-8.text-base.w-8.text-white.bg-red-500")
    btn_justificativa.click()
    time.sleep(1)
    input_element = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Informe...']")))
    js_code = f"navigator.clipboard.writeText('{ResponsesSPCAPITAL.JUSTIFICATIVA}')"
    driver.execute_script(js_code)
    input_element.send_keys(Keys.CONTROL, 'v')
    time.sleep(1)
    button_send = driver.find_element(By.XPATH, "//div[contains(@class, 'h-full relative w-full')]//button[normalize-space(text())='Salvar']")
    button_send.click()
    time.sleep(1)

    print("Passo 17: Preenchendo informações de transportador")
    containers = driver.find_elements(By.CSS_SELECTOR, "pgr-data-collect-execution-treatment-section .ng-select-container")
    if len(containers) >= 2:
        second_container = containers[1]
        driver.execute_script("arguments[0].scrollIntoView();", second_container)
        time.sleep(1)
        second_container.click()
    else:
        print("Não foram encontrados dois elementos")
        time.sleep(1)
    input_transportador = driver.switch_to.active_element
    WebDriverWait(driver, 10).until(EC.visibility_of(input_transportador))
    input_transportador.send_keys(ResponsesSPCAPITAL.TRANSPORTADOR)
    wait_element(".block-page-div-loader")
    input_transportador.send_keys(Keys.TAB)

    print("Passo 18: Preenchendo DESTINADOR")
    time.sleep(0.5)
    active_field = driver.switch_to.active_element 
    active_field.send_keys(ResponsesSPCAPITAL.DESTINADOR)
    wait_element(".block-page-div-loader")
    time.sleep(0.5)

    print("Passo 19: Confirmando tratamento")
    active_field.send_keys(Keys.TAB)
    active_field = driver.switch_to.active_element
    active_field.send_keys(Keys.ENTER)
    time.sleep(0.5)

    print("Passo 20: Inserindo quantidade anual")
    active_field = driver.switch_to.active_element
    active_field.send_keys(ResponsesSPCAPITAL.QUANTIDADE_ANUAL)
    time.sleep(0.5)

    print("Passo 21: Selecionando frequência")
    time.sleep(0.5)
    frequency_ng_select = driver.find_elements(By.CSS_SELECTOR, "pgr-data-collect-execution-treatment-section .ng-select-container")
    if frequency_ng_select:
        last_container = frequency_ng_select[-1]
        driver.execute_script("arguments[0].scrollIntoView();", last_container)
        time.sleep(1)
        last_container.click()
    else:
        print("Nenhum elemento com a classe .ng-select-container foi encontrado dentro de pgr-data-collect-execution-treatment-section")
    print("Passo 22: Confirmando frequência")
    time.sleep(1)
    last_container = driver.switch_to.active_element
    wait = WebDriverWait(driver, 10)
    wait.until(EC.visibility_of_element_located((By.XPATH, "//p[normalize-space(text())='Sob Demanda']")))
    last_container.send_keys(Keys.ENTER)

    print("Passo 23: Inserindo área responsável")
    grupo2 = wait.until(EC.presence_of_element_located((By.XPATH, "(//resource-custom-field-forms-section-groups)[2]")))
    input_responsible_area = grupo2.find_element(By.XPATH, ".//table[1]//ng-select")
    print("Área atual:", input_responsible_area.text)
    input_responsible_area.click()
    time.sleep(1)
    input_responsible_area = driver.switch_to.active_element
    input_responsible_area.send_keys(ResponsesSPCAPITAL.AREA_RESPONSAVEL)
    time.sleep(1)
    input_responsible_area.send_keys(Keys.ENTER)
    time.sleep(1)
    input_responsible_area.send_keys(Keys.TAB)
    time.sleep(1)

    print("Passo 24: Inserindo website de transporte")
    website_ng_select = driver.switch_to.active_element
    website_ng_select.send_keys(ResponsesSPCAPITAL.WEBSITE_TRANSPORTE)
    website_ng_select.send_keys(Keys.TAB)

    print("Passo 25: Inserindo website de destinação")
    website_ng_select = driver.switch_to.active_element
    website_ng_select.send_keys(ResponsesSPCAPITAL.WEBSITE_DESTINACAO)

    print("Passo 26: Selecionando opção 'Sim'")
    labels = driver.find_elements(By.XPATH, "(//resource-custom-field-forms-section-groups)[2]//select-field//label")
    for label in labels:
        try:
            span = label.find_element(By.XPATH, "./span[contains(text(), 'Sim')]")
            if span:
                label.click()
        except Exception:
            continue

    print("Passo 27: Enviando formulário")
    send_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Salvar e Enviar para Aprovação')]"))
    )
    send_button.click()
    try:
        send_button.click()
    except Exception:
        pass
    time.sleep(1)
    wait_element(".ngt-shining-xs")
    print("Passo 28: Formulário enviado com sucesso!")
    time.sleep(1)
    verify_hour()
    navigate_pages_until_pending(cycle, secund_page=True)


def close_pending_issues(rows, cycle):
    print("⚠️ There are pending issues! Starting the process to close them...")
    try:
        pending_row = None
        for row in rows:
            try:
                status_badge = row.find_element(By.XPATH, ".//div[contains(text(),'Pendente')]")
                if "PENDENTE" in status_badge.text.strip().upper():
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
        fill_form(cycle)
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
            status_badge = row.find_element(By.XPATH, ".//div[contains(text(),'Pendente')]")
            if "PENDENTE" in status_badge.text.strip().upper():
                pending_count += 1
            else:
                non_pending_count += 1
        except Exception:
            non_pending_count += 1
    print("Com pendência:", pending_count)
    print("Sem pendência:", non_pending_count)
    return pending_count, rows


def navigate_pages_until_pending(cycle, secund_page=False):
    if secund_page:
        try:            
            wait_element(".ngx-toastr.toast-info", 60)
        except:
            pass
        pending_count, rows = check_pgrs_pending()
        if pending_count < 1:
            filter_pending_reports()

    try:
        while True:
            pending_count, rows = check_pgrs_pending()
            if pending_count > 0:
                close_pending_issues(rows, cycle)
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
    print("🔹 Starting...")
    check_status()
    run_bot()
    
