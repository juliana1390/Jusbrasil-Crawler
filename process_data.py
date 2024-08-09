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
        return
        # return {
        #     "Número do processo": item['nro_processo'],
        #     "Erro": "Exceção",
        #     "Mensagem": str(e)
        # }
    
def process_data():
    url = "http://127.0.0.1:8000/api/process"

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
                
                # Salva a resposta em um arquivo JSON separado
                with open(output_filename, 'w', encoding='utf-8') as outfile:
                    json.dump(result, outfile, ensure_ascii=False, indent=4)
                
                print(f"Resultado salvo em: {output_filename}")

if __name__ == "__main__":
    process_data()