import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import json

# log para verificar successo ou falha
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

"""
Configura e retorna uma instância do navegador Chrome
rodando sem GUI - modo headless
"""
def driver_setup():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    return driver

"""
Busca dados no site do TJAL (Tribunal de Justiça de Alagoas)
com base no número do processo e grau fornecidos.
"""
def tjal_fetch_data(nro_processo, grau):
    if grau == 1:
        url = f"https://www2.tjal.jus.br/cpopg/open.do"
    else:
        url = f"https://www2.tjal.jus.br/cposg5/open.do"

    driver = driver_setup()
    driver.get(url)

    data = {} # inicializa um dicionário para armazenar os dados

    try:
        logger.info(f"Acessando URL: {url}")

        # espera a caixa de busca ser encontrada
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado"))
        )
        logger.info("Página carregada.")

        search_box.send_keys(nro_processo) # envia nro do processo
        search_box.send_keys(Keys.RETURN) # simula ENTER
        logger.info(f"A busca pelo processo {nro_processo} foi iniciada.")

        # coletar dados do processo
        data["classe"] = driver.find_element(By.ID, "classeProcesso").text
        logger.info("Classe do processo encontrada.")

        data["area"] = driver.find_element(By.ID, "areaProcesso").text
        logger.info("Área do processo encontrada.")

        data["assunto"] = driver.find_element(By.ID, "assuntoProcesso").text
        logger.info("Assunto encontrado.")

        data["data_distribuicao"] = driver.find_element(By.ID, "dataHoraDistribuicaoProcesso").text
        logger.info("Data/Hora de distribuição do processo encontrada.")

        data["juiz"] = driver.find_element(By.ID, "juizProcesso").text
        logger.info("Juíz encontrado.")

        data["valor_acao"] = driver.find_element(By.ID, "valorAcaoProcesso").text
        logger.info("Valor da ação encontrado.")

    except TimeoutException as e:
        logger.error(f"TimeoutException ocorreu: {e}", exc_info=True) # exc_info: capturar o rastreamento da pilha
        logger.debug(driver.page_source)  # depuracao da pagina
        data = {"erro": "TimeoutException: " + str(e)}

    except NoSuchElementException as e:
        logger.error(f"NoSuchElementException ocorreu: {e}", exc_info=True)
        data = {"erro": "NoSuchElementException: " + str(e)}

    except WebDriverException as e:
        logger.error(f"WebDriverException ocorreu: {e}", exc_info=True)
        data = {"erro": "WebDriverException: " + str(e)}

    except Exception as e:
        logger.error(f"Ocorreu um erro: {e}", exc_info=True)
        data = {"erro": str(e)}

    finally:
        driver.quit()
        logger.info("Driver encerrado.")

    return data