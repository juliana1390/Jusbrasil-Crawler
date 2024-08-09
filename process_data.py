import json
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_process_data(item, url):
    try:
        response = requests.post(url, json=item)
        print(f"Requisitando dados {item['nro_processo']}")
        if response.status_code == 200:
            response_data = response.json()
            return {
                "Número do processo": item['nro_processo'],
                "Consulta": response_data
            }
        else:
            print(f"Ocorreu um erro durante a pesquisa:\nProcesso: {item['nro_processo']}\nErro: {response.status_code}")
            return {
                "Número do processo": item['nro_processo'],
                "Erro": response.status_code,
                "Mensagem": response.text
            }
    except Exception as e:
        print(f"Exceção ao requisitar dados para {item['nro_processo']}: {str(e)}")
        return {
            "Número do processo": item['nro_processo'],
            "Erro": "Exceção",
            "Mensagem": str(e)
        }
    
def process_data():
    url = "http://127.0.0.1:8000/api/process"

    with open('input_file.json', 'r') as file:
        data = json.load(file)
        
        responses = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_item = {executor.submit(fetch_process_data, item, url): item for item in data}
        
        for future in as_completed(future_to_item):
            result = future.result() # se houver uma excecao, ela sera propagada
            if result:  # verificação para evitar adicionar None
                responses.append(result)

    # arquivo JSON com data e hora atual no nome, para salvar os resultados
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H:%M:%S")
    output_filename = f"response_{timestamp}.json"
    
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        json.dump(responses, outfile, ensure_ascii=False, indent=4)
    
    print(f"Respostas salvas em {output_filename}")

if __name__ == "__main__":
    process_data()