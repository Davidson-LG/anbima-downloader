import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configurações
os.makedirs('downloads', exist_ok=True)
hoje = datetime.now().strftime('%Y-%m-%d')

# Configuração do Chrome headless
chrome_options = Options()
chrome_options.add_argument('--headless=new')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
prefs = {
    "download.default_directory": os.path.abspath("downloads"),
    "download.prompt_for_download": False,
    "download.directory_upgrade": True
}
chrome_options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=chrome_options)

# Lista dos índices
indices = [
    ('IMA-B', '3', 'IMA-B'),
    ('IMA-B 5', '4', 'IMA-B5'),
    ('IMA-B 5+', '5', 'IMA-B5+')
]

# Navegação e download de cada índice
for nome_exibicao, valor_select, nome_arquivo in indices:
    try:
        driver.get('https://www.anbima.com.br/informacoes/ima/ima.asp')
        time.sleep(3)

        # Clique direto no botão de resultado
        driver.find_element(By.XPATH, '//input[@value="Resultado"]').click()
        time.sleep(2)

        # Seleciona o índice no formulário
        driver.find_element(By.NAME, 'indice').send_keys(valor_select)

        # Submete
        driver.find_element(By.XPATH, '//input[@value="Consultar"]').click()
        time.sleep(5)

        # Clica no link de Download
        driver.find_element(By.LINK_TEXT, 'Download').click()
        print(f'Download iniciado para {nome_exibicao}...')
        time.sleep(8)

        # Renomeia o arquivo
        arquivos = [f for f in os.listdir('downloads') if f.endswith('.csv')]
        if arquivos:
            arquivo_baixado = max([os.path.join('downloads', f) for f in arquivos], key=os.path.getctime)
            novo_nome = os.path.join('downloads', f"{nome_arquivo}_{hoje}.csv")
            os.rename(arquivo_baixado, novo_nome)
            print(f"Arquivo renomeado: {novo_nome}")
    except Exception as e:
        print(f"Erro em {nome_exibicao}: {str(e)}")

# Baixar o Quadro Resumo
try:
    driver.get("https://www.anbima.com.br/informacoes/ima/ima.asp")
    time.sleep(3)
    driver.find_element(By.XPATH, '//input[@value="Quadro resumo"]').click()
    time.sleep(2)
    driver.find_element(By.LINK_TEXT, 'Download').click()
    time.sleep(5)

    # Renomeia
    arquivos = [f for f in os.listdir('downloads') if f.endswith('.csv')]
    if arquivos:
        arquivo_baixado = max([os.path.join('downloads', f) for f in arquivos], key=os.path.getctime)
        novo_nome = os.path.join('downloads', f"Quadro_Resumo_{hoje}.csv")
        os.rename(arquivo_baixado, novo_nome)
        print(f"Quadro Resumo baixado: {novo_nome}")
except Exception as e:
    print(f"Erro no Quadro Resumo: {str(e)}")

driver.quit()

# Upload para o Google Drive
try:
    scopes = ["https://www.googleapis.com/auth/drive"]
    credentials_json = os.environ.get('GOOGLE_CREDENTIALS')
    if not credentials_json:
        raise Exception("Credenciais do Google não encontradas. Verifique seu GitHub Secrets.")

    credentials_info = json.loads(credentials_json)
    credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)

    service = build('drive', 'v3', credentials=credentials)

    folder_id = '1Q-wo4KFvGIZEEe9PoTMt_TPUK9Kuww_e'  # ID da pasta 'IMA’s'

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
