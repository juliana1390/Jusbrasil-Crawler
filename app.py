from flask import Flask, request, Response
from crawler import fetch_data
import json

app = Flask(__name__)

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
    if len(nro_processo) < 19:
        raise ValueError("Número do processo está no formato incorreto")

    numero_digito_ano_unificado = nro_processo[:13]
    jtr_numero_unificado = nro_processo[13:16]
    foro_numero_unificado = nro_processo[16:]

    tribunais = {
        '802': 'TJAL',
        '806': 'TJCE'
    }
    
    tribunal = tribunais.get(jtr_numero_unificado, None)

    if not tribunal:
        raise ValueError(f"Código do tribunal não identificado")

    return {
        "NumeroDigitoAnoUnificado": numero_digito_ano_unificado,
        "CodigoTribunal": jtr_numero_unificado,
        "ForoNumeroUnificado": foro_numero_unificado,
        "Tribunal": tribunal
    }

def generate_result(result_first_instance, result_second_instance):
    response_data = {
        "Primeiro Grau": result_first_instance,
        "Segundo Grau": result_second_instance
    }

    # conversao para JSON
    json_response = json.dumps(response_data, ensure_ascii=False, indent=4)

    return Response(
        json_response,
        mimetype='application/json; charset=utf-8'
    )

@app.route('/api/process', methods=['POST'])
def get_data():
    data = request.json
    nro_processo = data.get("nro_processo")

    try:
        parsed_data = parse_nro_processo(nro_processo)
    except ValueError as e:
        return Response(
            json.dumps({"erro": str(e)}),
            mimetype='application/json; charset=utf-8'
        ), 400

    tribunal = parsed_data["Tribunal"]
    nro_processo_modificado = parsed_data["NumeroDigitoAnoUnificado"] + parsed_data["ForoNumeroUnificado"]

    # chama o crawler
    if tribunal == 'TJAL':
        result_tjal1 = fetch_data(nro_processo_modificado, url_tjal_1)
        result_tjal2 = fetch_data(nro_processo_modificado, url_tjal_2)

        return generate_result(result_tjal1, result_tjal2)

    elif tribunal == 'TJCE':
        result_tjce1 = fetch_data(nro_processo_modificado, url_tjce_1)
        result_tjce2 = fetch_data(nro_processo_modificado, url_tjce_2)

        return generate_result(result_tjce1, result_tjce2)

if __name__ == "__main__":
    app.run(debug=True)