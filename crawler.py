import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
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
            "classe": find_text(soup, "classeProcesso", "N/A"),
            "area": find_text(soup, "areaProcesso", "N/A"),
            "assunto": find_text(soup, "assuntoProcesso", "N/A"),
            "data_distribuicao": find_text(soup, "dataHoraDistribuicaoProcesso", "N/A"),
            "juiz": find_text(soup, "juizProcesso", "N/A"),
            "valor_acao": find_text(soup, "valorAcaoProcesso", "N/A")
        }
    elif grau == "segundo_grau":
        return {
            "classe": find_text(soup, "classeProcesso", "N/A"),
            "area": find_text(soup, "areaProcesso", "N/A"),
            "assunto": find_text(soup, "assuntoProcesso", "N/A"),
            "relator": find_text(soup, "relatorProcesso", "N/A"),
            "valor_acao": find_text(soup, "valorAcaoProcesso", "N/A")
        }
    return {}

def extract_partes(soup):
    partes = {}
    try:
        # acessa a tabela das partes
        tabela_partes = soup.find(id="tableTodasPartes")
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
        partes = None
    return partes

def extract_movimentacoes(soup):
    movimentacoes = []
    try:
        # acessa a tabela de movimentacoes
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
        movimentacoes = None
    return movimentacoes

def interact_with_modal(driver, wait):
    try:
        modal_element = wait.until(EC.presence_of_element_located((By.ID, "modalIncidentes")))
        radio_button = modal_element.find_element(By.ID, "processoSelecionado")
        radio_button.click()
        select_button = modal_element.find_element(By.ID, "botaoEnviarIncidente")
        select_button.click()
        wait.until(EC.staleness_of(modal_element))  # aguarda o modal ser fechado
        
        # Recarregar o HTML e o BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        logger.info("Interagido com o modal com sucesso.")
    except (TimeoutException, NoSuchElementException):
        logger.info("Modal não encontrado. Continuando sem interagir com o modal.")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    return soup

def fetch_data(nro_processo, url):
    # cpopg = Consulta de Processos de 1º Grau // cposg5 = Consulta de Processos de 2º Grau
    grau = "primeiro_grau" if "cpopg" in url else "segundo_grau"

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
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
        print("carregou soup")
        # verifica a existencia de mensagem de erro, caso o nro do processo esteja errado
        try:
            erro_element = driver.find_element(By.ID, "spwTabelaMensagem")
            erro_msg = erro_element.text.strip()
            if erro_msg:
                logger.error("Processo %s não encontrado no %s, ou número está incorreto.", nro_processo, grau)
                data = {}
                return
        except NoSuchElementException:
            logger.info("Nenhum erro encontrado. Continuando a extração dos dados.")

        print("antes modal")
        # interage com o modal, se necessario
        soup = interact_with_modal(driver, wait)
        print("apos modal")
        # coleta os dados do processo
        data = extract_data_from_soup(soup, grau)
        data['partes'] = extract_partes(soup)
        data['movimentacoes'] = extract_movimentacoes(soup)
        logger.info("Dados coletados.")
        print(data)
    except (TimeoutException, WebDriverException) as e:
        logger.error("Erro ocorreu durante a busca: %s", e)
        data = {}

    return {
        "Dados Processuais": data
    }