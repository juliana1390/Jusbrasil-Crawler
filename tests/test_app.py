import pytest
import json
from app import app
# from unittest.mock import patch

@pytest.fixture
def client():
    app.testing = True
    client = app.test_client()
    yield client

def test_valid_process(client):
    response = client.post('/api/process', json={"nro_processo": "07108025520188020001"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "Primeiro Grau" in data
    assert "Segundo Grau" in data

# def test_invalid_process(client):
#     response = client.post('/api/process', json={"nro_processo": "12345"})
#     assert response.status_code == 400
#     data = json.loads(response.data)
#     assert "erro" in data
#     assert data["erro"] == "Número do processo está no formato incorreto"

# def test_empty_process_number(client):
#     response = client.post('/api/process', json={"nro_processo": ""})
#     assert response.status_code == 400
#     data = json.loads(response.data)
#     assert "erro" in data
#     assert data["erro"] == "Número do processo não pode estar vazio"

# def test_non_existent_process(client):
#     response = client.post('/api/process', json={"nro_processo": "99999999999999999999"})
#     assert response.status_code == 400
#     data = json.loads(response.data)
#     assert "erro" in data
#     assert data["erro"] == "Processo não encontrado"


# def test_process_number_with_unexpected_characters(client):
#     response = client.post('/api/process', json={"nro_processo": "0710802552018802@0001"})
#     assert response.status_code == 400
#     data = json.loads(response.data)
#     assert "erro" in data
#     assert data["erro"] == "Número do processo contém caracteres inválidos"

# @patch('app.process_data', side_effect=TimeoutError)
# def test_server_unavailable(mock_process_data, client):
#     # simula a indisponibilidade do servidor
#     response = client.post('/api/process', json={"nro_processo": "07108025520188020001"})
#     assert response.status_code == 503
#     data = json.loads(response.data)
#     assert "erro" in data
#     assert data["erro"] == "Serviço indisponível"