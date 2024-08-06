import requests
import json

def send_data_to_api():
    url = "http://0.0.0.0:8000/api/process"

    with open('input_data.json', 'r') as file:
        data = json.load(file)
        
        for item in data:
            response = requests.post(url, json=item)
            print(f"Requisitando dados do processo: {item['nro_processo']}")
            if response.status_code == 200:
                print("Resposta:")
                print(response.json())
                print("\n\n")
            else:
                print(f"Erro: {response.status_code}")
                print(response.text)

if __name__ == "__main__":
    send_data_to_api()
