import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup

# configura o log para verificar sucesso ou falha
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_data_from_soup(soup, grau):
    if grau == "primeiro_grau":
        return {
            "classe": soup.find(id="classeProcesso").get_text(strip=True),
            "area": soup.find(id="areaProcesso").get_text(strip=True),
            "assunto": soup.find(id="assuntoProcesso").get_text(strip=True),
            "data_distribuicao": soup.find(id="dataHoraDistribuicaoProcesso").get_text(strip=True),
            "juiz": soup.find(id="juizProcesso").get_text(strip=True),
            "valor_acao": soup.find(id="valorAcaoProcesso").get_text(strip=True)
        }
    elif grau == "segundo_grau":
        return {
            "classe": soup.find("span", title=True).get_text(strip=True),
            "area": soup.find(id="areaProcesso").get_text(strip=True),
            "assunto": soup.find(id="assuntoProcesso").get_text(strip=True),
            "relator": soup.find(id="relatorProcesso").get_text(strip=True),
            "valor_acao": soup.find(id="valorAcaoProcesso").get_text(strip=True)
        }
    return {}

def tjal_fetch_data(nro_processo):
    url_grau_1 = "https://www2.tjal.jus.br/cpopg/open.do"
    url_grau_2 = "https://www2.tjal.jus.br/cposg5/open.do"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    # dicionarios separados para armazenar resultados
    grau_1 = {}
    grau_2 = {}

    try:
        # procura no primeiro grau
        logger.info("Acessando URL: %s", url_grau_1)
        driver.get(url_grau_1)
        logger.info("Página carregada para o primeiro grau.")
        
        # insere o numero do processo no campo de busca
        search_box = wait.until(EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado")))
        search_box.send_keys(nro_processo)
        search_box.send_keys(Keys.RETURN)
        logger.info("A busca pelo processo %s foi iniciada no primeiro grau.", nro_processo)
        
        try:
            # extrai o HTML da pagina e cria o BeautifulSoup
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # coleta os dados do processo
            grau_1 = extract_data_from_soup(soup, "primeiro_grau")
            logger.info("Dados coletados para o primeiro grau.")
        except NoSuchElementException as e:
            logger.error("NoSuchElementException ocorreu para o primeiro grau: %s", e)
            grau_1 = {"error": f"NoSuchElementException ocorreu: {str(e)}"}
        
        # procura no segundo grau
        logger.info("Acessando URL: %s", url_grau_2)
        driver.get(url_grau_2)
        logger.info("Página carregada para o segundo grau.")
        
        # insere o numero do processo no campo de busca
        search_box = wait.until(EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado")))
        search_box.send_keys(nro_processo)
        search_box.send_keys(Keys.RETURN)
        logger.info("A busca pelo processo %s foi iniciada no segundo grau.", nro_processo)

        try:
            logger.info("Esperando o modal ser carregado.")
            modal_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".modal-content")))
            logger.info("Modal carregado.")
            select_button = modal_element.find_element(By.XPATH, '//button[text()="Selecionar"]')
            select_button.click()
            logger.info("Botão 'Selecionar' clicado.")

            # extrai o HTML da pagina e cria o BeautifulSoup
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            # coleta os dados do processo
            grau_2 = extract_data_from_soup(soup, "segundo_grau")
            logger.info("Dados coletados para o segundo grau.")
        except NoSuchElementException as e:
            logger.error("NoSuchElementException ocorreu para o segundo grau: %s", e)
            grau_2 = {"error": f"NoSuchElementException ocorreu: {str(e)}"}
        
    except TimeoutException:
        logger.error("TimeoutException ocorreu.")
    except WebDriverException as e:
        logger.error("WebDriverException ocorreu: %s", e)
    finally:
        driver.quit()
        logger.info("Driver encerrado.")

    # retorna os resultados separados por grau
    return {
        "primeiro_grau": grau_1,
        "segundo_grau": grau_2
    }
