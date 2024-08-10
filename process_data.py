import json
import logging
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# configura o logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("process_data.log"),  # log em arquivo
                        logging.StreamHandler()  # log no console
                    ])
logger = logging.getLogger(__name__)

def fetch_process_data(item, url):
    try:
        response = requests.post(url, json=item)
        logger.info(f"Requisitando dados {item['nro_processo']}")
        if response.status_code == 200:
            response_data = response.json()
            return {
                "Número do processo": item['nro_processo'],
                "Consulta": response_data
            }
        else:
            response_data = response.json()
            logger.error(f"Ocorreu um erro durante a pesquisa: "
                          f"Processo: {item['nro_processo']} | "
                          f"Erro: {response.status_code} | "
                          f"Mensagem: {response.text}")
            return
    except Exception as e:
        logger.exception(f"Exceção ao requisitar dados para {item['nro_processo']}: {str(e)}")
        return
    
def process_data():
    url = "http://flask_app:5000/api/process" # docker

    with open('input_file.json', 'r') as file:
        data = json.load(file)

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_item = {executor.submit(fetch_process_data, item, url): item for item in data}
        
        for future in as_completed(future_to_item):
            result = future.result()  # se houver uma exceção, ela será propagada
            if result:  # verificação para evitar adicionar None
                # cria um timestamp para o nome do arquivo
                now = datetime.now()
                timestamp = now.strftime("%Y-%m-%d_%H:%M:%S")
                process_number = result["Número do processo"]
                output_filename = f"processo_{process_number}_({timestamp}).json"
                
                # salva a resposta em um arquivo JSON separado
                with open(output_filename, 'w', encoding='utf-8') as outfile:
                    json.dump(result, outfile, ensure_ascii=False, indent=4)
                
                logger.info(f"\nResultado salvo em: {output_filename}")

if __name__ == "__main__":
    process_data()