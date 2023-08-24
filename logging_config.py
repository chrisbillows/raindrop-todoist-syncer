import logging
import sys
from loguru import logger

class InterceptHandler(logging.Handler):
    """
    Class to re-route logs created by third party modules to loguru.
    """
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def configure_logging():
    logger.remove(0)  # Remove loguru's default logger
    
    # Intercept third party logs 
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.root.setLevel(logging.DEBUG)
    
    # Configure seperate file handling if req'd e.g. for monitoring third party modules
    # for debugging notifications I'm unaware of
    file_handler = logging.FileHandler('builtin_logging.log')
    file_handler.setLevel(logging.DEBUG)
    logging.root.addHandler(file_handler)
    
    
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
    )
    
    logger.add(
        "log.log", 
        rotation="500 MB", 
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
    )
        
    logger.add(
        "log_serialized.log", 
        rotation="500 MB", 
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
        serialize=True
    )
    