from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from datetime import datetime, timedelta
import os

# Função para calcular os últimos 5 dias úteis
def get_last_5_business_days():
    business_days = []
    date = datetime.now()
    while len(business_days) < 5:
        date -= timedelta(days=1)
        # 0 = Segunda, 1 = Terça, ..., 5 = Sábado, 6 = Domingo
        if date.weekday() < 5:  # Dias úteis (segunda a sexta)
            business_days.append(date.strftime("%d/%m/%Y"))
    return business_days

# Configurações do Selenium
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Rodar sem interface gráfica
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Diretório para salvar os arquivos
download_dir = "/path/to/save/files"  # Ajuste para o diretório desejado
prefs = {"download.default_directory": download_dir}
options.add_experimental_option("prefs", prefs)

# Inicializa o driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# URL do site
url = "https://www.anbima.com.br/pt_br/informar/ima-resultados-diarios.htm"
driver.get(url)

# Índices que queremos baixar
indices = ["Quadro Resumo", "IMA-B", "IMA-B 5", "IMA-B 5+"]

# Obter os últimos 5 dias úteis
dates = get_last_5_business_days()

# Loop para cada data
for date in dates:
    print(f"Baixando relatórios para {date}...")
    
    # Campo de data
    date_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='dd/mm/aaaa']"))
    )
    date_field.clear()
    date_field.send_keys(date)

    # Loop para cada índice
    for index in indices:
        # Selecionar o índice
        index_radio = driver.find_element(By.XPATH, f"//label[contains(text(), '{index}')]/preceding-sibling::input[@type='radio']")
        index_radio.click()

        # Selecionar o formato XLS
        xls_radio = driver.find_element(By.XPATH, "//label[contains(text(), 'XLS')]/preceding-sibling::input[@type='radio']")
        xls_radio.click()

        # Botão "Download"
        download_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Download')]")
        download_button.click()

        # Aguardar o download (ajuste o tempo conforme necessário)
        time.sleep(5)

# Fechar o driver
driver.quit()

print("Downloads concluídos!")
