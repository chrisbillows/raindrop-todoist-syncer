import logging
import sys

from loguru import logger


from raindrop_todoist_syncer.config import SystemConfig


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


def configure_logging(system_config: SystemConfig):
    # Remove loguru's default handler (which logs to stderr with colors)
    logger.remove()

    # Create the logs directory if it doesn't exist
    system_config.logs_dir.mkdir(parents=True, exist_ok=True)
    log_file_builtins = system_config.logs_dir / "builtins.log"
    log_file = system_config.logs_dir / "log.log"

    # ------- Python logging config -------
    # Route standard `logging` (e.g. from third-party libs) into loguru via
    # InterceptHandler
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    logging.root.setLevel(logging.DEBUG)
    # Additionally log raw built-in logging messages to a separate file. `requests`
    # does this, so include to ensure all requests logs are intercepted.
    file_handler = logging.FileHandler(log_file_builtins)
    file_handler.setLevel(logging.DEBUG)
    logging.root.addHandler(file_handler)

    # ------- Loguru config -------
    # Console logs go to stdout (as configured)
    # If no `format=` is specified, loguru enables colored output by default.
    # Uncomment `format=` to disable colors or customize layout.
    logger.add(
        sys.stdout,
        level="INFO",
    )
    logger.add(
        log_file,
        rotation="5 MB",
        level="DEBUG",
    )
