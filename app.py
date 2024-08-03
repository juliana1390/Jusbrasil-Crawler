from flask import Flask, request, jsonify
from crawlers import tjal_fetch_data

app = Flask(__name__)

@app.route('/api/process', methods=['POST'])
def get_data():
    data = request.json
    nro_processo = data.get("nro_processo")
    tribunal = data.get("tribunal")
    grau = data.get("grau", 1)

    if tribunal == "TJAL":
        result = tjal_fetch_data(nro_processo, grau)
    else:
        return jsonify({"erro": "Tribunal nao abrangido pela busca"}), 400
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)