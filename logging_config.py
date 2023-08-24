from loguru import logger
import sys

def configure_logging():
    logger.remove(0)  # Remove loguru's default logger

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
    