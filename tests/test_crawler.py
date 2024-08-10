import pytest
from app.crawler import fetch_data

def test_fetch_data():
    url = "https://www2.tjal.jus.br/cpopg/open.do"
    nro_processo = "07108025520188020001"
    result = fetch_data(nro_processo, url)
    assert "Dados Processuais" in result
