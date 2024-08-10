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

# configura o log para verificar sucesso ou falha
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_data_from_soup(soup, grau):
    # lida com valores nao encontrados
    def find_text(soup, selector, default=""):
        element = soup.find(id=selector)
        return element.get_text(strip=True) if element else default
    
    if grau == "primeiro_grau":
        return {
            "Classe": find_text(soup, "classeProcesso", "N/A"),
            "Área": find_text(soup, "areaProcesso", "N/A"),
            "Assunto": find_text(soup, "assuntoProcesso", "N/A"),
            "Data da Distribuição": find_text(soup, "dataHoraDistribuicaoProcesso", "N/A"),
            "Juiz": find_text(soup, "juizProcesso", "N/A"),
            "Valor da Ação": find_text(soup, "valorAcaoProcesso", "N/A")
        }
    elif grau == "segundo_grau":
        return {
            "Classe": find_text(soup, "classeProcesso", "N/A"),
            "Área": find_text(soup, "areaProcesso", "N/A"),
            "Assunto": find_text(soup, "assuntoProcesso", "N/A"),
            "Órgão Julgador": find_text(soup, "orgaoJulgadorProcesso", "N/A"),
            "Relator": find_text(soup, "relatorProcesso", "N/A"),
            "Valor da Ação": find_text(soup, "valorAcaoProcesso", "N/A")
        }
    return {}

def extract_partes(soup):
    partes = {}
    try:
        # acessa a tabela das partes
        tabela_partes = soup.find(id="tableTodasPartes") or soup.find(id="tablePartesPrincipais")

        if tabela_partes:
            for parte in tabela_partes.find_all('tr'):
                cols = parte.find_all('td')
                if len(cols) >= 2:
                    nome = cols[0].get_text(strip=True)
                    advogado = cols[1].get_text(strip=True)
                    partes[nome] = f"{advogado}"
        else:
            logger.warning("Tabela de partes não encontrada.")
    except Exception as e:
        logger.error("Erro ao extrair partes: %s", e)
        partes = {}
    return partes

def extract_movimentacoes(soup):
    movimentacoes = []
    try:
        # Acessa a tabela de movimentações
        tabela_movimentacoes = soup.find(id="tabelaTodasMovimentacoes")
        if tabela_movimentacoes:
            rows = tabela_movimentacoes.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    data = cols[0].get_text(strip=True)
                    descricao = " ".join([x.strip() for x in cols[2].get_text(strip=True).split("\n") if x.strip() != ""])
                    movimentacoes.append({
                        'data': data,
                        'descricao': descricao
                    })
        else:
            logger.warning("Tabela de movimentações não encontrada.")
    except Exception as e:
        logger.error("Erro ao extrair movimentações: %s", e)
        movimentacoes = []
    return movimentacoes

def interact_with_modal(driver, wait):
    try:
        modal_element = wait.until(EC.presence_of_element_located((By.ID, "modalIncidentes")))
        radio_button = modal_element.find_element(By.ID, "processoSelecionado")
        radio_button.click()
        select_button = modal_element.find_element(By.ID, "botaoEnviarIncidente")
        select_button.click()
        wait.until(EC.staleness_of(modal_element))  # aguarda o modal ser fechado
        
        # recarrega o HTML e o BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        logger.info("Página com modal.")
    except (TimeoutException, NoSuchElementException):
        logger.info("Página sem modal.")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup

def process_ul(grau, driver, soup):
    ul_elements = soup.find_all('ul', class_='unj-list-row')
    
    # pega url atual e faz parse para cortar o endereco da home
    url = driver.current_url
    parsed_url = urlparse(url)

    # construindo a URL principal (esquema + netloc)
    url_principal = f"{parsed_url.scheme}://{parsed_url.netloc}"
 
    if not ul_elements:
        logger.warning("Nenhum elemento <ul> com a classe 'unj-list-row' encontrado.")
        return []

    results = []

    for item in ul_elements:
        lis = item.find_all('li')
        for dados in lis:
            link_element = dados.find('a', class_='linkProcesso')
            if link_element:
                link = link_element.get('href')
                if link:
                    # verifica se o link e um caminho relativo
                    if link.startswith('/'):
                        full_url = f"{url_principal}{link}"
                    else:
                        full_url = link

                    logger.info("Abrindo link: %s", full_url)
                    driver.get(full_url)

                    # coleta os dados da nova pagina
                    html = driver.page_source
                    soup_new = BeautifulSoup(html, 'html.parser')

                    data = extract_data_from_soup(soup_new, grau)
                    data['Partes'] = extract_partes(soup_new)
                    data['Movimentações'] = extract_movimentacoes(soup_new)

                    results.append(data)
            else:
                logger.warning("Link com a classe 'linkProcesso' não encontrado em <li>: %s", dados.get_text(strip=True))

    return results


def fetch_data(nro_processo, url):
    # cpopg = Consulta de Processos de 1º Grau // cposg5 = Consulta de Processos de 2º Grau
    grau = "primeiro_grau" if "cpopg" in url else "segundo_grau"

    # configura opcoes do chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # configura o servico do chromedriver
    service = Service(ChromeDriverManager().install())
    # service = Service('/usr/local/bin/chromedriver-linux64/chromedriver')

    # inicializa o webdriver com as opcoes e servico configurados
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)
    data = {}
    
    try:
        logger.info("Acessando URL: %s", url)
        driver.get(url)
        
        search_box = wait.until(EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado")))
        search_box.send_keys(nro_processo)
        search_box.send_keys(Keys.RETURN)
        logger.info("A busca pelo processo %s foi iniciada no %s.", nro_processo, grau)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # verifica a existencia de mensagem de erro, caso o nro do processo esteja errado
        try:
            erro_element = driver.find_element(By.ID, "spwTabelaMensagem")
            erro_msg = erro_element.text.strip()
            if erro_msg:
                logger.error("Processo %s não encontrado no %s, ou número está incorreto.", nro_processo, grau)
                return {"Dados Processuais": {}}
        except NoSuchElementException:
            logger.info("Nenhum erro encontrado. Continuando a extração dos dados.")

        # interage com o modal, se necessario
        soup = interact_with_modal(driver, wait)

        # verifica ul
        results = process_ul(grau, driver, soup)
        
        if not results:
            # coleta os dados do processo se <ul> não for encontrado
            logger.info("Nenhuma lista de instâncias do processo.")
            data = extract_data_from_soup(soup, grau)
            data['Partes'] = extract_partes(soup)
            data['Movimentações'] = extract_movimentacoes(soup)
            results = [data]
            logger.info("Dados coletados.")

        return {"Dados Processuais": results}
    
    except (TimeoutException, WebDriverException) as e:
        logger.error("Erro ocorreu durante a busca: %s", e)
        return {"Dados Processuais": {}}

    finally:
        driver.quit()