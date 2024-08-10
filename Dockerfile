# Estagio base
FROM python:3.11-slim AS base

WORKDIR /app

ENV PYTHONPATH=/app

# Copia o arquivo de requisitos e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala pacotes necessaios para o Selenium
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && apt-get install -y google-chrome-stable

# Instalação do ChromeDriver usando WebDriverManager
RUN pip install webdriver-manager && python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"

# Copia arquivos do projeto
COPY . /app

# Estagio de testes
FROM base AS test

# Executa os testes com pytest
RUN pytest --maxfail=1 --disable-warnings -q

# Estagio final para produção
FROM base AS final

# Exponhe a porta 5000 para o aplicativo Flask
EXPOSE 5000

# Comando para executar o aplicativo com Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "wsgi:app"]
