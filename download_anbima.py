import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

# Cria a pasta de downloads, se não existir
os.makedirs('downloads', exist_ok=True)

# Configurações do Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')  # roda em modo invisível
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

prefs = {
    "download.default_directory": os.path.abspath("downloads"),
    "download.prompt_for_download": False,
    "directory_upgrade": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Inicia o Chrome
driver = webdriver.Chrome(options=chrome_options)

# Acessa a página direta
driver.get('https://www.anbima.com.br/informacoes/ima/ima.asp')

# Pequena pausa para carregar
time.sleep(2)

# Lista dos índices que queremos baixar
indices = [
    ('IMA-B', '3', 'IMA-B'),
    ('IMA-B 5', '4', 'IMA-B5'),
    ('IMA-B 5+', '5', 'IMA-B5+')
]

# Data de hoje para nomear os arquivos
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

# ----------------- Parte Google Drive -----------------

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json

# Pega o JSON de credenciais do ambiente
credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')

if not credentials_json:
    raise ValueError("GOOGLE_CREDENTIALS_JSON não encontrado nas variáveis de ambiente!")

# Cria um arquivo temporário para usar as credenciais
with open('temp_credentials.json', 'w') as f:
    f.write(credentials_json)

scopes = ["https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_file('temp_credentials.json', scopes=scopes)
gc = gspread.authorize(credentials)
service = build('drive', 'v3', credentials=credentials)

# ID da pasta do Drive (corrigido!)
folder_id = '1Q-wo4KFvGIZEEe9PoTMt_TPUK9Kuww_e'

# Upload dos arquivos
def upload_to_drive(filepath, folder_id):
    filename = os.path.basename(filepath)
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filepath, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f'Arquivo {filename} enviado para o Google Drive.')

# Enviar todos arquivos da pasta downloads/
downloads_path = 'downloads'
for file in os.listdir(downloads_path):
    if file.endswith('.csv'):
        upload_to_drive(os.path.join(downloads_path, file), folder_id)

# Apaga o arquivo temporário de credenciais
os.remove('temp_credentials.json')
