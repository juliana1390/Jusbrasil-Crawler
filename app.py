from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, Response, jsonify
from utils.logger_config import setup_logger
from crawler import fetch_data
from datetime import datetime
import json
import os

app = Flask(__name__)
logger = setup_logger(__name__)

url_tjal_1 = "https://www2.tjal.jus.br/cpopg/open.do"
url_tjal_2 = "https://www2.tjal.jus.br/cposg5/open.do"
url_tjce_1 = "https://esaj.tjce.jus.br/cpopg/open.do"
url_tjce_2 = "https://esaj.tjce.jus.br/cposg5/open.do"


"""
exemplo:

numero do processo: 0710802-55.2018.8.02.0001

Número: 0710802
Dígito Verificador: 55
Ano: 2018
Órgão: 8
Código do Tribunal: 02
Código da Vara: 0001
-----------------------------------
request: 07108025520188020001

numero_digito_ano_unificado: 0710802552018
jtr_numero_unificado: 802
foro_numero_unificado: 0001

parse_nro_processo = deixa o input no formato adequado para a busca,
ja que o valor de orgao e tribunal ja consta na pagina web
"""
def parse_nro_processo(nro_processo):
    cleaned_number = nro_processo.replace('-', '').replace('.', '')

    numero_digito_ano_unificado = cleaned_number[:13]
    jtr_numero_unificado = cleaned_number[13:16]
    foro_numero_unificado = cleaned_number[16:]

    tribunais = {
        '802': 'TJAL',
        '806': 'TJCE'
    }
    
    tribunal = tribunais.get(jtr_numero_unificado, None)
    nro_processo_modificado = numero_digito_ano_unificado + foro_numero_unificado

    return {
        "NumeroDigitoAnoUnificado": nro_processo_modificado,
        "Tribunal": tribunal,
        "NroCompleto": nro_processo
    }

def generate_result(nro_processo, result_primeiro_grau, result_segundo_grau):
    response_data = {
        "Número do Processo": nro_processo,
        "Primeiro Grau": result_primeiro_grau,
        "Segundo Grau": result_segundo_grau
    }

    # converte para JSON
    json_response = json.dumps(response_data, ensure_ascii=False, indent=4)

    return Response(
        json_response,
        mimetype='application/json; charset=utf-8'
    )

@app.route('/api/process', methods=['POST'])
def process_data():
    with open('input/input_file.json', 'r') as file:
        data = json.load(file)

    with ThreadPoolExecutor(max_workers=5) as executor:        
        future_to_item = {executor.submit(get_data, item): item for item in data}

        try:
            for future in as_completed(future_to_item):  # fornece os futures na ordem em que terminam
                response = future.result()  # resultado da tarefa associada ao future. Se gerou excecao, propagada-se
                if response:
                    # parse dados do JSON do objeto Response
                    result = response.get_json()
                    if result:
                        now = datetime.now()
                        timestamp = now.strftime("%d-%m-%Y_%H:%M:%S")
                        process_number = result.get("Número do Processo")
                        print(process_number)
                        output_filename = f"processo_{process_number}_({timestamp}).json"

                        # salva o arquivo no diretorio de saida
                        output_path = os.path.join('output', output_filename)
                    
                        # salva a resposta em um arquivo JSON
                        with open(output_path, 'w', encoding='utf-8') as outfile:
                            json.dump(result, outfile, ensure_ascii=False, indent=4)
                        
                        logger.info(f"Resultado salvo em: {output_path}\n")
                        return jsonify(result), 200
        except:
            return Response(
            json.dumps({'erro': 'Processo não encontrado'}),
            mimetype='application/json; charset=utf-8'
        ), 400

def get_data(item):
    nro_processo = item.get("nro_processo")

    try:
        parse_data = parse_nro_processo(nro_processo)
    except ValueError as e:
        return Response(
            json.dumps({'erro': str(e)}),
            mimetype='application/json; charset=utf-8'
        ), 400
    
    if parse_data['Tribunal'] == 'TJAL':
        result_tjal1 = fetch_data(parse_data['NumeroDigitoAnoUnificado'], parse_data['NroCompleto'], url_tjal_1)
        result_tjal2 = fetch_data(parse_data['NumeroDigitoAnoUnificado'], parse_data['NroCompleto'], url_tjal_2)
        return generate_result(nro_processo, result_tjal1, result_tjal2)

    elif parse_data['Tribunal'] == 'TJCE':
        result_tjce1 = fetch_data(parse_data['NumeroDigitoAnoUnificado'], parse_data['NroCompleto'], url_tjce_1)
        result_tjce2 = fetch_data(parse_data['NumeroDigitoAnoUnificado'], parse_data['NroCompleto'], url_tjce_2)
        return generate_result(nro_processo, result_tjce1, result_tjce2)    

    else:
        return Response(
            json.dumps({'erro': 'Processo não encontrado'}),
            mimetype='application/json; charset=utf-8'
        ), 400

if __name__ == "__main__":
    app.run(debug=True)
