import datetime
import traceback
from loguru import logger

from raindrop_todoist_syncer.db_manage import DatabaseManager
from raindrop_todoist_syncer.rd_credentials import RaindropCredentialsManager
from raindrop_todoist_syncer.rd_process import RaindropsProcessor
from raindrop_todoist_syncer.rd_token import RaindropAccessTokenRefresher
from raindrop_todoist_syncer.raindrop import (
    EnvironmentVariablesFileManager,
    RaindropClient,
)
from raindrop_todoist_syncer.td_task_create import TodoistTaskCreator

from raindrop_todoist_syncer.logging_config import configure_logging

configure_logging()


def main():
    """
    Main function that does the following steps:
    - Checks for a stale token and refreshes if necessary.
    - Get all raindrops from the RaindropClient.
    - Process these raindrops.
    - For each processed task, create a task in Todoist.
    """
    rc = RaindropClient()
    rcm = RaindropCredentialsManager()
    evfm = EnvironmentVariablesFileManager()
    ratr = RaindropAccessTokenRefresher(rcm, evfm)
    dbm = DatabaseManager()

    if rc.stale_token():
        ratr.refresh_token_process_runner()
    all_raindrops = rc.get_all_raindrops()
    rp = RaindropsProcessor(all_raindrops)
    tasks_to_create = rp.newly_favourited_raindrops_extractor()
    for task in tasks_to_create:
        task_creator = TodoistTaskCreator(task)
        task_creator.create_task()
        dbm.update_database([task])


if __name__ == "__main__":
    start = datetime.datetime.now()
    logger.info(f"Run started at {start.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        main()
        end = datetime.datetime.now()
        duration = (end - start).total_seconds()
        logger.info(
            f"Run completed at {end.strftime('%Y-%m-%d %H:%M:%S')} | Run time {duration:.2f} seconds"
        )
    except Exception as e:
        end = datetime.datetime.now()
        duration = (end - start).total_seconds()
        logger.error(f"{e}\n{traceback.format_exc()}\n")
        logger.info(
            f"Run terminated at {end.strftime('%Y-%m-%d %H:%M:%S')} | Run time to failure {duration:.2f} seconds"
        )
