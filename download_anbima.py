import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configurações iniciais
os.makedirs('downloads', exist_ok=True)

# Configurações do Chrome
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

prefs = {
    "download.default_directory": os.path.abspath("downloads"),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True
}
chrome_options.add_experimental_option("prefs", prefs)

# Inicia o Chrome
driver = webdriver.Chrome(options=chrome_options)

# Lista dos índices
indices = [
    ('IMA-B', '3', 'IMA-B'),
    ('IMA-B 5', '4', 'IMA-B5'),
    ('IMA-B 5+', '5', 'IMA-B5+')
]

hoje = datetime.now().strftime('%Y-%m-%d')

for nome_exibicao, valor_select, nome_arquivo in indices:
    try:
        driver.get('https://www.anbima.com.br/informacoes/ima/ima.asp')
        time.sleep(3)

        # Seleciona "Resultados"
        select_visualizacao = Select(driver.find_element(By.NAME, 'opcao'))
        select_visualizacao.select_by_value('resultado')

        # Seleciona o índice
        select_indice = Select(driver.find_element(By.NAME, 'indice'))
        select_indice.select_by_value(valor_select)

        # Clica em Consultar
        driver.find_element(By.XPATH, '//input[@type="submit" and @value="Consultar"]').click()
        time.sleep(5)

        # Download
        driver.find_element(By.LINK_TEXT, 'Download').click()
        print(f'Download iniciado para {nome_exibicao}...')
        time.sleep(8)

        # Renomeia arquivo
        arquivos = [f for f in os.listdir('downloads') if f.endswith('.csv')]
        if arquivos:
            arquivo_baixado = max(
                [os.path.join('downloads', f) for f in arquivos],
                key=os.path.getctime
            )
            novo_nome = os.path.join('downloads', f"{nome_arquivo}_{hoje}.csv")
            os.rename(arquivo_baixado, novo_nome)
            print(f"Arquivo renomeado: {novo_nome}")

    except Exception as e:
        print(f"Erro em {nome_exibicao}: {str(e)}")

driver.quit()

# Upload para Google Drive
try:
    scopes = ["https://www.googleapis.com/auth/drive"]

    # Pega o conteúdo do segredo da variável de ambiente
    credentials_info = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
    credentials = service_account.Credentials.from_service_account_info(credentials_info, scopes=scopes)

    service = build('drive', 'v3', credentials=credentials)

    # ATENÇÃO: Substitua pelo ID real da sua pasta (não a URL)
    folder_id = '1Q-wo4KFvGIZEEe9PoTMt_TPUK9Kuww_e'

    for file in os.listdir('downloads'):
        if file.endswith('.csv'):
            file_metadata = {
                'name': file,
                'parents': [folder_id]
            }
            media = MediaFileUpload(
                os.path.join('downloads', file),
                mimetype='text/csv'
            )
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f"Upload concluído: {file}")

except Exception as e:
    print(f"Erro no upload: {str(e)}")
