# # Use uma imagem base com Python
# FROM python:3.11-slim

# # Defina o diretório de trabalho no contêiner
# WORKDIR /app

# # Copie o arquivo de requisitos e instale as dependências
# COPY requirements.txt requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

# RUN apt-get update && \
#     apt-get install -y wget gnupg && \
#     wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
#     sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list' && \
#     apt-get update && \
#     apt-get install -y google-chrome-stable

# RUN chmod +x /root/.wdm/drivers/chromedriver/linux64/114.0.5735.90/chromedriver
    

# # Copie o restante do código do aplicativo
# COPY . .

# # Expose port 5000 for the Flask app
# EXPOSE 5000

# # Command to run the application with Gunicorn
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "wsgi:app"]


# Use Python slim image
FROM python:3.11-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install necessary packages for Selenium
RUN apt-get update && \
    apt-get install -y wget gnupg && \
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && apt-get install -y google-chrome-stable

# Install ChromeDriver using WebDriverManager during runtime
RUN pip install webdriver-manager && python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"

# Remove the chmod command or ensure correct path
# RUN chmod +x /root/.wdm/drivers/chromedriver/linux64/114.0.5735.90/chromedriver

# Copy project files
COPY . .

# Expose port 5000 for the Flask app
EXPOSE 5000

# Command to run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "wsgi:app"]
