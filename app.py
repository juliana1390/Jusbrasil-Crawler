from flask import Flask, request, Response
from tjal_crawler import tjal_fetch_data
from tjce_crawler import tjce_fetch_data
import json

app = Flask(__name__)

"""
exemplo:

numero do processo: 0710802-55.2018.8.02.0001

Número: 0710802
Dígito Verificador: 55
Ano: 2018
Comarca: 8
Código do Tribunal: 02
Código da Vara: 0001
-----------------------------------
request: 07108025520188020001

numero_digito_ano_unificado: 0710802552018
jtr_numero_unificado: 802
foro_numero_unificado: 0001

parse_nro_processo = deixa a requisicao no formato adequado para a busca,
ja que o valor de comarca e tribunal ja consta na pagina web
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
    
    # chama a funcao de busca apropriada
    if tribunal == 'TJAL':
        nro_processo_modificado = parsed_data["NumeroDigitoAnoUnificado"] + parsed_data["ForoNumeroUnificado"]
        fetch_data_function = tjal_fetch_data
    elif tribunal == 'TJCE':
        nro_processo_modificado = parsed_data["NumeroDigitoAnoUnificado"] + parsed_data["ForoNumeroUnificado"]
        fetch_data_function = tjce_fetch_data

    result = fetch_data_function(nro_processo_modificado)
    
    # conversao JSON
    json_response = json.dumps(result, ensure_ascii=False, indent=4)

    return Response(
        json_response,
        mimetype='application/json; charset=utf-8'
    )

if __name__ == "__main__":
    app.run(debug=True)