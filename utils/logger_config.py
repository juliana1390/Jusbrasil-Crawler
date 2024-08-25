import logging
import os

def setup_logger(name, log_dir='logs'):
    # cria um diretório de logs se nao existir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # define o nome do arquivo de log
    log_file = os.path.join(log_dir, f"{name}.log")

    # cria o logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # configura o FileHandler e o Formatter
    file_handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # adiciona o FileHandler e o StreamHandler ao logger
    logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler())

    return logger
