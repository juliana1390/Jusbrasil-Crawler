import requests
import json
from datetime import datetime

def process_data():
    url = "http://127.0.0.1:8000/api/process"

    with open('input_file.json', 'r') as file:
        data = json.load(file)
        
        responses = []
        
        for item in data:
            response = requests.post(url, json=item)
            print(f"Requisitando dados {item['nro_processo']}")
            if response.status_code == 200:
                response_data = response.json()
                response_data["nro_processo"] = item['nro_processo']
                responses.append(response_data)
            else:
                responses.append({
                    "nro_processo": item['nro_processo'],
                    "error": response.status_code,
                    "message": response.text
                })

    # arquivo JSON com data e hora atual no nome, para salvar os resultados
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = f"response_{timestamp}.json"
    
    with open(output_filename, 'w', encoding='utf-8') as outfile:
        json.dump(responses, outfile, ensure_ascii=False, indent=4)
    
    print(f"Respostas salvas em {output_filename}")

if __name__ == "__main__":
    process_data()


   