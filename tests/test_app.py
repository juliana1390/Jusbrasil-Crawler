import pytest
import json
from web_scraper.app import app

@pytest.fixture
def client():
    app.testing = True
    client = app.test_client()
    yield client

def test_valid_process(client):
    response = client.post('/api/process', json={"nro_processo": "0709255-67.2024.8.02.0001"})
    assert response.status_code == 200

def test_invalid_process(client):
    response = client.post('/api/process', json={"nro_processo": "12345"})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "erro" in data
    assert data["erro"] == "Número do processo está no formato incorreto"

def test_empty_process_number(client):
    response = client.post('/api/process', json={"nro_processo": ""})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "erro" in data
    assert data["erro"] == "Número do processo está no formato incorreto"

# def test_server_unavailable(mocker, client):
#     mocker.patch('web_scraper.app.get_data', side_effect=TimeoutError)
#     response = client.post('/api/process', json={"nro_processo": "0709255-67.2024.8.02.0001"})
#     assert response.status_code == 503
#     data = json.loads(response.data)
#     assert "erro" in data
#     assert data["erro"] == "Serviço indisponível"