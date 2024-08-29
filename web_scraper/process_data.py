from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger_config import setup_logger
from datetime import datetime
import requests
import json
import os

logger = setup_logger(__name__)

def fetch_process_data(item, url):
    try:
        response = requests.post(url, json=item)
        logger.info(f"Requisitando dados {item['nro_processo']}")

        if response.status_code == 200:
            try:
                response_data = response.json()
                return {
                    "Número do processo": item['nro_processo'],
                    "Consulta": response_data
                }
            except json.JSONDecodeError:
                logger.error(f"Resposta não JSON para o processo {item['nro_processo']}")
                return None
        else:
            try:
                response_data = response.json()
                logger.error(f"Ocorreu um erro durante a pesquisa: "
                            f"Processo: {item['nro_processo']} | "
                            f"Erro: {response.status_code} | "
                            f"Mensagem: {response_data}")
            except json.JSONDecodeError:
                logger.error(f"Ocorreu um erro durante a pesquisa: "
                              f"Processo: {item['nro_processo']} | "
                              f"Erro: {response.status_code} | "
                              f"Mensagem: {response.text}")
            return None
        
    except Exception as e:
        logger.exception(f"Exceção ao requisitar dados para {item['nro_processo']}: {str(e)}")
        return None
    
def process_data():
    url = "http://web:5000/api/process" # docker

    with open('input/input_file.json', 'r') as file:
        data = json.load(file)
        logger.info("Arquivo de input lido.")

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_item = {executor.submit(fetch_process_data, item, url): item for item in data}

        for future in future_to_item:
            logger.info(f"{future} criada!")

        for future in as_completed(future_to_item): # fornece os futures na ordem em que terminam
            result = future.result()  # resultado da tarefa associada ao future. Se gerou excecao, propagada-se
            if result:
                # cria um timestamp para o nome do arquivo
                now = datetime.now()
                timestamp = now.strftime("%d-%m-%Y_%H:%M:%S")
                nro_processo = result["Número do processo"]
                output_filename = f"processo_{nro_processo}_({timestamp}).json"

                # salva o arquivo no diretorio de saida
                output_path = os.path.join('output', output_filename)
            
                # salva a resposta em um arquivo JSON
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    json.dump(result, outfile, ensure_ascii=False, indent=4)
                
                logger.info(f"\nResultado salvo em: {output_path}")

if __name__ == "__main__":
    process_data()