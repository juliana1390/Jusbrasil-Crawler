import pytest
from web_scraper.crawler import fetch_data

def test_fetch_data():
    url = "https://www2.tjal.jus.br/cpopg/open.do"
    nro_digito_ano_unif = "07092556720248020001"
    nro_completo= "0709255-67.2024.8.02.0001 "
    result = fetch_data(nro_digito_ano_unif, nro_completo, url)
    assert result is not None

def test_invalid_url():
    url = "https://invalid-url.example.com"
    nro_digito_ano_unif = "07092556720248020001"
    nro_completo= "0709255-67.2024.8.02.0001"
    result = fetch_data(nro_digito_ano_unif, nro_completo, url)
    assert result is None or "erro" in result
