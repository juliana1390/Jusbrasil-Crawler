import requests
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_process_data(item, url):
    response = requests.post(url, json=item)
    print(f"Requisitando dados {item['nro_processo']}")
    if response.status_code == 200:
        response_data = response.json()
        return {
            "Número do processo": item['nro_processo'],
            "Dados": response_data
        }
    else:
        return {
            "Número do processo": item['nro_processo'],
            "Erro": response.status_code,
            "Mensagem": response.text
        }



def process_data():
    url = "http://127.0.0.1:8000/api/process"

    with open('input_file.json', 'r') as file:
        data = json.load(file)
        
        responses = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_item = {executor.submit(fetch_process_data, item, url): item for item in data}
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    responses.append(result)
                except Exception as exc:
                    responses.append({
                        "Número do processo": item['nro_processo'],
                        "Erro": "Exception",
                        "Mensagem": str(exc)
                    })

    # arquivo JSON com data e hora atual no nome, para salvar os resultados
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H:%M:%S")
    output_filename = f"response_{timestamp}.json"
    
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        json.dump(responses, outfile, ensure_ascii=False, indent=4)
    
    print(f"Respostas salvas em {output_filename}")

if __name__ == "__main__":
    process_data()


   