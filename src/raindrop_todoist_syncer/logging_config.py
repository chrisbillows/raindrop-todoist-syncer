import logging
import os
import sys
from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Class to intercept and re-route logs created by third party modules to loguru. Will
    also intercept any logs created by logging.{level}.
    """

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def configure_logging():
    logger.remove(0)  # Remove loguru's default logger
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Intercept third party logs
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.root.setLevel(logging.DEBUG)

    # Configure seperate file handling if req'd e.g. for monitoring third party modules
    # for debugging notifications I'm unaware of
    file_handler = logging.FileHandler("logs/builtin_logging.log")
    file_handler.setLevel(logging.DEBUG)
    logging.root.addHandler(file_handler)

    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
    )

    logger.add(
        "logs/log.log",
        rotation="5 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
    )

    logger.add(
        "logs/log_serialized.log",
        rotation="5 MB",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="DEBUG",
        serialize=True,
    )
