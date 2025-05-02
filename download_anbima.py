# Instalação de pacotes necessária no ambiente (no requirements ou em runtime)
# pip install gspread google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import json
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- Parte 1: Baixar arquivos da ANBIMA ---

# Cria a pasta de downloads, se não existir
os.makedirs('downloads', exist_ok=True)

# Configurações do Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

prefs = {
    "download.default_directory": os.path.abspath("downloads"),
    "download.prompt_for_download": False,
    "directory_upgrade": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Inicia o navegador
driver = webdriver.Chrome(options=chrome_options)

# Acessa o site
driver.get('https://www.anbima.com.br/informacoes/ima/ima.asp')
time.sleep(2)

# Lista de índices para download
indices = [
    ('IMA-B', '3', 'IMA-B'),
    ('IMA-B 5', '4', 'IMA-B5'),
    ('IMA-B 5+', '5', 'IMA-B5+')
]

hoje = datetime.now().strftime('%Y-%m-%d')

for nome_exibicao, valor_select, nome_arquivo in indices:
    try:
        driver.get('https://www.anbima.com.br/informacoes/ima/ima.asp')
        time.sleep(2)

        select_visualizacao = Select(driver.find_element(By.NAME, 'opcao'))
        select_visualizacao.select_by_value('resultado')

        select_indice = Select(driver.find_element(By.NAME, 'indice'))
        select_indice.select_by_value(valor_select)

        driver.find_element(By.XPATH, '//input[@type="submit" and @value="Consultar"]').click()
        time.sleep(3)

        driver.find_element(By.LINK_TEXT, 'Download').click()
        print(f'Download iniciado para {nome_exibicao}...')
        time.sleep(5)

        arquivos = os.listdir('downloads')
        arquivos_csv = [arq for arq in arquivos if arq.lower().endswith('.csv')]

        if arquivos_csv:
            arquivo_baixado = max([os.path.join('downloads', f) for f in arquivos_csv], key=os.path.getctime)
            novo_nome = os.path.join('downloads', f"{nome_arquivo}_{hoje}.csv")
            os.rename(arquivo_baixado, novo_nome)
            print(f"Arquivo renomeado para {novo_nome}")
        else:
            print(f"Nenhum arquivo CSV encontrado para {nome_exibicao}.")

    except Exception as e:
        print(f"Erro ao processar {nome_exibicao}: {e}")

driver.quit()
print("Todos downloads concluídos!")

# --- Parte 2: Enviar para o Google Drive ---

# Lê o segredo do JSON armazenado no ambiente
service_account_info = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
scopes = ["https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)

# Inicializa a API do Drive
service = build('drive', 'v3', credentials=credentials)

# ID da pasta de destino no Drive (somente o ID, sem link ou parâmetros)
folder_id = '1Q-wo4KFvGIZEEe9PoTMt_TPUK9Kuww_e'  # <--- ajuste aqui

def upload_to_drive(filepath, folder_id):
    filename = os.path.basename(filepath)
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f'Arquivo {filename} enviado para o Google Drive.')

downloads_path = 'downloads'
for file in os.listdir(downloads_path):
    if file.endswith('.csv'):
        upload_to_drive(os.path.join(downloads_path, file), folder_id)
