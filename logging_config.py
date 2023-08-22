import logging
from pythonjsonlogger import jsonlogger

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
    formatter = jsonlogger.JsonFormatter(log_format)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    file_handler = logging.FileHandler("application.log")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
