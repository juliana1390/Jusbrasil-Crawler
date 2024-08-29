#!/bin/sh
# Inicia o Flask
gunicorn --bind 0.0.0.0:5000 --timeout 120 --workers 5 wsgi:app &

# Executa o script Python
python3 web_scraper/process_data.py
