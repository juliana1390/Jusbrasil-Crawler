import os
import json
import logging
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# configura o logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("logs/process_data.log"),  # log em arquivo
                        logging.StreamHandler()  # log no console
                    ])
logger = logging.getLogger(__name__)

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
    url = "http://flask_app:5000/api/process" # docker

    with open('input/input_file.json', 'r') as file:
        data = json.load(file)

    """
        Estre trecho permite executar tarefas em paralelo usando um conjunto fixo de threads. 
        - 'max_workers=5' define o número máximo de threads que podem ser usadas simultaneamente.
            5 threads podem processar requisições ao mesmo tempo.

        - 'submit' é o método que envia a função fetch_process_data para ser executada em uma thread separada.
            Passa item e url como argumentos da função quando a tarefa for executada.
            Retorna um objeto Future, que representa a tarefa pendente.

        Dicionário 'future_to_item':
            A chave é o Future retornado pela submit e o valor é o item correspondente de 'data' (dados).
            Cada Future é uma instância da tarefa pendente (uma requisição em execução).
            
            Exemplo de um future:
                {<Future at 0x7f627a621850 state=running>: {'nro_processo': '00507582220218060028'}, ... }

                Future: <Future at 0x7f627a621850 state=running>, Item: {'nro_processo': '00507582220218060028'}
                    O endereço hexadecimal (0x7f627a621850, ...) é uma referência ao objeto Future na memória.
                    Item é o dicionário associado a esse Future, contendo os dados que foram enviados para a API.
    """
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_item = {executor.submit(fetch_process_data, item, url): item for item in data}

        for future in as_completed(future_to_item): # fornece os futures na ordem em que terminam
            result = future.result()  # resultado da tarefa associada ao future. Se gerou excecao, propagada-se
            if result:
                # cria um timestamp para o nome do arquivo
                now = datetime.now()
                timestamp = now.strftime("%d-%m-%Y_%H:%M:%S")
                process_number = result["Número do processo"]
                output_filename = f"processo_{process_number}_({timestamp}).json"

                # salva o arquivo no diretorio de saida
                output_path = os.path.join('output', output_filename)
            
                
                # salva a resposta em um arquivo JSON
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    json.dump(result, outfile, ensure_ascii=False, indent=4)
                
                logger.info(f"\nResultado salvo em: {output_path}")

if __name__ == "__main__":
    process_data()