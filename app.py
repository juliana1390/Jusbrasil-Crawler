from flask import Flask, request, Response
from crawlers import tjal_fetch_data
import json

app = Flask(__name__)

# rota /api/process definida, aceitando apenas requisições POST
@app.route('/api/process', methods=['POST'])

# extrai os dados da requisicao
def get_data():
    data = request.json
    nro_processo = data.get("nro_processo")
    tribunal = data.get("tribunal")
    grau = data.get("grau")

    if tribunal != 'TJAL':
        return Response(
            json.dumps({"erro": "Tribunal não suportado"}),
            mimetype='application/json; charset=utf-8'
        ), 400
    
    result = tjal_fetch_data(nro_processo, grau)
    
    # conversao
    json_response = json.dumps(result, ensure_ascii=False)

    return Response(
        json_response,
        mimetype='application/json; charset=utf-8'
    )

if __name__ == "__main__":
    app.run(debug=True)