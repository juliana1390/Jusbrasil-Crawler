from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from utils.logger_config import setup_logger
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# configura nome para logger
logger = setup_logger(__name__)

def find_text(soup, selector, default=""):
    element = soup.find(id=selector)
    return element.get_text(strip=True) if element else default

def extract_data_from_soup(soup, grau, nro_completo):
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
    logger.info(f"Dados processuais genéricos coletados para o processo {nro_completo} no {grau}!")
    return {**common_fields, **specific_fields.get(grau, {})}

def extract_partes(soup, grau):
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
            logger.info(f"Dados das partes coletados no {grau}!")
        else:
            logger.warning("Tabela de partes não encontrada.")
    except Exception as e:
        logger.error("Erro ao extrair partes: %s", e)
    return partes

def extract_movimentacoes(soup, grau):
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
            logger.info(f"Movimentações processuais coletadas no {grau}!\n")
        else:
            logger.warning("Tabela de movimentações não encontrada.")
    except Exception as e:
        logger.error("Erro ao extrair movimentações: %s", e)
    return movimentacoes

def interact_with_modal(driver, wait):
    try:
        logger.info("\n=== Iniciando extração de dados! ===")
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
    logger.info("Dados coletados em todas as instâncias!\n")
    return results
