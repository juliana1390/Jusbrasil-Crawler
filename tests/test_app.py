import pytest
import json
from app.app import app

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

def test_invalid_process(client):
    response = client.post('/api/process', json={"nro_processo": "invalid_format"})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "erro" in data
    assert data["erro"] == "Número do processo está no formato incorreto"
