from flask import Flask, request, Response
from web_scraper.crawler import fetch_data
import json
import re

app = Flask(__name__)

urls = {"tjal1": "https://www2.tjal.jus.br/cpopg/open.do", "tjal2": "https://www2.tjal.jus.br/cposg5/open.do",
        "tjce1": "https://esaj.tjce.jus.br/cpopg/open.do", "tjce2": "https://esaj.tjce.jus.br/cposg5/open.do"}

def parse_nro_processo(nro_processo):
    """
        ex. numero do processo: 0710802-55.2018.8.02.0001

        Número: 0710802
        Dígito Verificador: 55
        Ano: 2018
        Órgão: 8
        Código do Tribunal: 02
        Código da Vara: 0001
    """
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
def get_data():
    data = request.json
    nro_processo = data.get("nro_processo")
    regex_number = r'^(\d{7})-(\d{2})\.(\d{4})\.(\d{1})\.(\d{2})\.(\d{4})$'
    
    if not re.match(regex_number, nro_processo):
        return Response (
            json.dumps({'erro': 'Número do processo está no formato incorreto'}),
            mimetype='application/json; charset=utf-8'
        ), 400

    try:
        parse_data = parse_nro_processo(nro_processo)
    except ValueError as ve:
        return Response(
            json.dumps({'erro': str(ve)}),
            mimetype='application/json; charset=utf-8'
        ), 400

    if parse_data['Tribunal'] == 'TJAL':
        result_tjal1 = fetch_data(parse_data['NumeroDigitoAnoUnificado'], parse_data['NroCompleto'], urls.get("tjal1"))
        result_tjal2 = fetch_data(parse_data['NumeroDigitoAnoUnificado'], parse_data['NroCompleto'], urls.get("tjal2"))
        return generate_result(nro_processo, result_tjal1, result_tjal2)

    elif parse_data['Tribunal'] == 'TJCE':
        result_tjce1 = fetch_data(parse_data['NumeroDigitoAnoUnificado'], parse_data['NroCompleto'], urls.get("tjce1"))
        result_tjce2 = fetch_data(parse_data['NumeroDigitoAnoUnificado'], parse_data['NroCompleto'], urls.get("tjce2"))
        return generate_result(nro_processo, result_tjce1, result_tjce2)    

    else:
        return Response(
                json.dumps({'erro': 'Tribunal incorreto'}),
                mimetype='application/json; charset=utf-8'
            ), 400

if __name__ == "__main__":
    app.run(debug=True)