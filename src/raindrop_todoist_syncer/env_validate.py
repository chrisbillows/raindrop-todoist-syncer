import re

from loguru import logger

from raindrop_todoist_syncer.logging_config import configure_logging
from raindrop_todoist_syncer.raindrop import (
    EnvironmentVariablesFileManager,
    RaindropCredentialsManager,
)
from src.raindrop_todoist_syncer.todoist import TodositCredentialsManager

configure_logging()


def is_uuid(value):
    uuid_regex = re.compile(
        r"^[0-9a-f]{8}-"
        r"[0-9a-f]{4}-"
        r"4[0-9a-f]{3}-"
        r"[89ab][0-9a-f]{3}-"
        r"[0-9a-f]{12}\Z",
        re.I,
    )
    return bool(uuid_regex.match(value))


def sense_check_raindrop_client_id(rcm: RaindropCredentialsManager):
    if len(rcm.RAINDROP_CLIENT_ID) != 24:
        print("Warning: RAINDROP_CLIENT_ID length is not 24 characters.")
    if not rcm.RAINDROP_CLIENT_ID.isalnum():
        print("Warning: RAINDROP_CLIENT_ID is not alphanumeric.")
    logger.info("Sense checked RAINDROP_CLIENT_ID.")


def sense_check_raindrop_client_secret(rcm: RaindropCredentialsManager):
    if len(rcm.RAINDROP_CLIENT_SECRET) != 36:
        logger.warning(
            "RAINDROP_CLIENT_SECRET length is not 36 characters which may mean it is incorrect."
        )
    if not is_uuid(rcm.RAINDROP_CLIENT_SECRET):
        raise ValueError(
            "RAINDROP_CLIENT_SECRET is not in UUID format which may mean it is incorrect."
        )
    logger.info("Sense checked RAINDROP_CLIENT_SECRET.")


def required_env_variables_checker(
    rcm: RaindropCredentialsManager, tcm: TodositCredentialsManager
):
    """Validate the .env file contains all required environment variables.

    Raises
    ------
    ValueError
        If a required environment variable is not present in the `.env` file.
    """
    logger.info("Verifing all required environment variables.")
    if not rcm.RAINDROP_CLIENT_ID:
        raise ValueError("RAINDROP_CLIENT_ID is not set.")
    if not rcm.RAINDROP_CLIENT_SECRET:
        raise ValueError("RAINDROP_CLIENT_SECRET is not set.")
    if not rcm.RAINDROP_REFRESH_TOKEN:
        raise ValueError("RAINDROP_REFRESH_TOKEN is not set.")
    if not rcm.RAINDROP_ACCESS_TOKEN:
        raise ValueError("RAINDROP_ACCESS_TOKEN is not set.")
    if not tcm.TODOIST_API_KEY:
        raise ValueError("TODOIST_API_KEY is not set.")


def main():
    logger.info("Verifying .env configuration.")
    evfm = EnvironmentVariablesFileManager()
    rcm = RaindropCredentialsManager(evfm)
    tcm = TodositCredentialsManager()
    required_env_variables_checker(rcm, tcm)
    sense_check_raindrop_client_id(rcm)
    sense_check_raindrop_client_secret(rcm)
    logger.info(".env configuration verified.")


if __name__ == "__main__":
    main()
