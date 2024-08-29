from utils.data_extractors import extract_data_from_soup, extract_partes, extract_movimentacoes, interact_with_modal, process_ul
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from utils.logger_config import setup_logger
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup

# configura nome para logger
logger = setup_logger(__name__)

def fetch_data(nro_processo, nro_completo, url):
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
        logger.info(f'\n=== Busca pelo processo {nro_completo} ===')
        logger.info("Acessando URL: %s", url)
        driver.get(url)
        
        search_box = wait.until(EC.presence_of_element_located((By.ID, "numeroDigitoAnoUnificado")))
        search_box.send_keys(nro_processo)
        search_box.send_keys(Keys.RETURN)
        logger.info(f'Busca iniciada no {grau}!')

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        try:
            erro_element = driver.find_element(By.ID, "spwTabelaMensagem")
            erro_msg = erro_element.text.strip()
            if erro_msg:
                logger.warning(f'Processo {nro_completo} não encontrado.\n')
                return {"Dados Processuais": {}}
        except NoSuchElementException:
            logger.info("Nenhum erro encontrado. Continuando extração.")

        soup = interact_with_modal(driver, wait)

        # funcao utilizada em segundo grau para retornar mais de um resultado
        results = process_ul(grau, driver, soup)
        
        if not results:
            logger.info("Nenhuma lista de instâncias encontrada.\n")
            data = extract_data_from_soup(soup, grau, nro_completo)
            data['Partes'] = extract_partes(soup, grau)
            data['Movimentações'] = extract_movimentacoes(soup, grau)
            results = [data]

        return {"Dados Processuais": results}

    except (TimeoutException, WebDriverException) as e:
        logger.error("Erro durante a busca: Verifique os dados e a url inseridos na busca.\n")
        return{'erro': 'Verifique os dados e a url inseridos na busca.'}
    
    except TimeoutError:
        logger.error("Serviço indisponível\n")
        # return Response(
        #         json.dumps({'erro': 'Serviço indisponível'}),
        #         mimetype='application/json; charset=utf-8'
        #     ), 503
        return {'erro': 'Serviço indisponível'}

    finally:
        driver.quit()