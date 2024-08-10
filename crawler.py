import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# passar informacoes atraves do logging

# configura o logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("crawler_data.log"),  # log em arquivo
                        logging.StreamHandler()  # log no console
                    ])

logger = logging.getLogger(__name__)

def find_text(soup, selector, default=""):
    element = soup.find(id=selector)
    return element.get_text(strip=True) if element else default

def extract_data_from_soup(soup, grau):
    common_fields = {
        "Classe": find_text(soup, "classeProcesso", "N/A"),
        "Área": find_text(soup, "areaProcesso", "N/A"),
        "Assunto": find_text(soup, "assuntoProcesso", "N/A"),
        "Valor da Ação": find_text(soup, "valorAcaoProcesso", "N/A"),
    }
    
    specific_fields = {
        "primeiro_grau": {
            "Data da Distribuição": find_text(soup, "dataHoraDistribuicaoProcesso", "N/A"),
            "Juiz": find_text(soup, "juizProcesso", "N/A"),
        },
        "segundo_grau": {
            "Órgão Julgador": find_text(soup, "orgaoJulgadorProcesso", "N/A"),
            "Relator": find_text(soup, "relatorProcesso", "N/A"),
        }
    }
    
    return {**common_fields, **specific_fields.get(grau, {})} # desempacota os dicionarios e retorna

def extract_partes(soup):
    partes = {}
    try:
        table_partes = soup.find(id="tableTodasPartes") or soup.find(id="tablePartesPrincipais")
        if table_partes:
            for parte in table_partes.find_all('tr'):
                cols = parte.find_all('td')
                if len(cols) >= 2:
                    nome = cols[0].get_text(strip=True)
                    advogado = cols[1].get_text(strip=True)
                    
                    # verifica se ha "Advogado:" ou "Advogada:" e adiciona " | " para separar as strings
                    if "Advogado:" in advogado:
                        advogado = advogado.replace("Advogado:", " | Advogado: ")
                    elif "Advogada:" in advogado:
                        advogado = advogado.replace("Advogada:", " | Advogada: ")
                    
                    partes[nome] = advogado
        else:
            logger.warning("Tabela de partes não encontrada.")
    except Exception as e:
        logger.error("Erro ao extrair partes: %s", e)
    return partes

def extract_movimentacoes(soup):
    movimentacoes = []
    try:
        table_movimentacoes = soup.find(id="tabelaTodasMovimentacoes")
        if table_movimentacoes:
            for row in table_movimentacoes.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 3:
                    data = cols[0].get_text(strip=True)
                    descricao = " ".join([x.strip() for x in cols[2].get_text(strip=True).split("\n") if x.strip()])
                    movimentacoes.append({'data': data, 'descricao': descricao})
        else:
            logger.warning("Tabela de movimentações não encontrada.")
    except Exception as e:
        logger.error("Erro ao extrair movimentações: %s", e)
    return movimentacoes

def interact_with_modal(driver, wait):
    try:
        modal_element = wait.until(EC.presence_of_element_located((By.ID, "modalIncidentes")))
        radio_button = modal_element.find_element(By.ID, "processoSelecionado")
        radio_button.click()
        select_button = modal_element.find_element(By.ID, "botaoEnviarIncidente")
        select_button.click()
        wait.until(EC.staleness_of(modal_element))  # aguarda o modal ser fechado
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        logger.info("Interação com modal bem sucedida.")
    except (TimeoutException, NoSuchElementException):
        logger.info("Modal não encontrado. Continuando...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup

def process_ul(grau, driver, soup):
    ul_elements = soup.find_all('ul', class_='unj-list-row')
    parsed_url = urlparse(driver.current_url)
    url_principal = f"{parsed_url.scheme}://{parsed_url.netloc}"
 
    if not ul_elements:
        return []

    results = []

    for item in ul_elements:
        lis = item.find_all('li')
        for data in lis:
            link_element = data.find('a', class_='linkProcesso')
            if link_element:
                full_url = f"{url_principal}{link_element.get('href')}" if link_element.get('href').startswith('/') else link_element.get('href')
                logger.info("Abrindo link: %s", full_url)
                driver.get(full_url)
                soup_new = BeautifulSoup(driver.page_source, 'html.parser')
                data = extract_data_from_soup(soup_new, grau)
                data['Partes'] = extract_partes(soup_new)
                data['Movimentações'] = extract_movimentacoes(soup_new)
                results.append(data)
            else:
                logger.warning("Link com a classe 'linkProcesso' não encontrado em <li>: %s", data.get_text(strip=True))

    return results

def fetch_data(nro_processo, url):
    # cpopg = Consulta de Processos de 1º Grau // cposg5 = Consulta de Processos de 2º Grau
    grau = "primeiro_grau" if "cpopg" in url else "segundo_grau"
    
    # inicializa opcoes / driver
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)

    # dicionario para armazenar os resultados
    data = {}

    try:
        logger.info("Acessando URL: %s", url)
        driver.get(url)
        
        search_box = wait.until(EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado")))
        search_box.send_keys(nro_processo)
        search_box.send_keys(Keys.RETURN)
        logger.info("Busca pelo processo %s iniciada.", nro_processo)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        try:
            erro_element = driver.find_element(By.ID, "spwTabelaMensagem")
            erro_msg = erro_element.text.strip()
            if erro_msg:
                logger.warning("Processo %s não encontrado.", nro_processo)
                return {"Dados Processuais": {}}
        except NoSuchElementException:
            logger.info("Nenhum erro encontrado. Continuando extração.")

        soup = interact_with_modal(driver, wait)

        # funcao utilizada em segundo grau para retornar mais de um resultado
        results = process_ul(grau, driver, soup)
        
        if not results:
            logger.info("Nenhuma lista de instâncias encontrada.")
            data = extract_data_from_soup(soup, grau)
            data['Partes'] = extract_partes(soup)
            data['Movimentações'] = extract_movimentacoes(soup)
            results = [data]

        return {"Dados Processuais": results}

    except (TimeoutException, WebDriverException) as e:
        logger.error("Erro durante a busca: %s", e)
        return {"Dados Processuais": {}}

    finally:
        driver.quit()