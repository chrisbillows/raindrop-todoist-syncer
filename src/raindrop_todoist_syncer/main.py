import argparse
import datetime
import traceback

from loguru import logger

from raindrop_todoist_syncer.config import UserConfig, SystemConfig
from raindrop_todoist_syncer.db_manage import DatabaseManager
from raindrop_todoist_syncer.logging_config import configure_logging
from raindrop_todoist_syncer.plist import AutomationManager
from raindrop_todoist_syncer.rd_process import RaindropsProcessor
from raindrop_todoist_syncer.rd_client import RaindropClient
from raindrop_todoist_syncer.td_task import TodoistTaskCreator


def fetch_raindrops_and_create_tasks(
    user_config: UserConfig,
    raindrop_client: RaindropClient,
    database_manager: DatabaseManager,
) -> None:
    """
    Driver function to fetch raindrops, create tasks and update database.

    Parameters
    ----------
    user_config: UserConfig
        A UserConfig object.
    raindrop_client: RaindropClient
        A RaindropClient object.
    database_manager: DatabaseManager
        A Database Manager object
    """
    all_raindrops = raindrop_client.get_all_raindrops()
    rp = RaindropsProcessor(user_config, all_raindrops)
    tasks_to_create = rp.newly_favourited_raindrops_extractor()
    for task in tasks_to_create:
        task_creator = TodoistTaskCreator(user_config, task)
        task_creator.create_task()
        database_manager.update_database([task])


def driver(args: argparse.Namespace, user_config: UserConfig):
    """
    Driver function.

    Parameters
    ----------
    args: argparse.Namespace
        The parsed args.
    system_config: SystemConfig
        A user's system config object.

    Raises
    ------
    NotImplementedError
        Catch a command added to argparse but not configured in the dispatcher.
    """
    logger.info(f"Parsed args were {args}")

    if args.command == "run":
        rc = RaindropClient(user_config)
        dbm = DatabaseManager(user_config)
        fetch_raindrops_and_create_tasks(user_config, rc, dbm)

    elif args.command == "automate_enable":
        am = AutomationManager(user_config)
        am.activate_automatic_rd_fetch_and_task_creation()

    elif args.command == "automate_disable":
        am = AutomationManager(user_config)
        am.deactivate_automatic_rd_fetch_and_task_creation()

    else:
        logger.error(f"Unhandled command: {args.command}")
        raise NotImplementedError(f"No handler defined for command: {args.command}")


def parse_args() -> None:
    """
    Parse args.
    """
    border = "=" * 25
    parser = argparse.ArgumentParser(
        prog="Raindrop Todoist Syncer",
        description=(
            f"{border}\n Raindrop Todoist Syncer\n{border}\n\n"
            f"Create todoist tasks from favourited raindrops"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Fetch raindrops and create tasks")
    subparsers.add_parser("automate_enable", help="Activate automation")
    subparsers.add_parser("automate_disable", help="Deactivate automation")

    # Default to 'run' if no command is given
    parser.set_defaults(command="run")

    return parser.parse_args()


def main() -> None:
    """
    Entry point for raindrop todoist syncer.
    """
    system_config = SystemConfig()
    configure_logging(system_config)
    logger.debug(system_config)

    args = parse_args()
    user_config = UserConfig.from_env_file(system_config)
    driver(args, user_config)


if __name__ == "__main__":
    start = datetime.datetime.now()
    logger.info(f"Run started at {start.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        main()
        end = datetime.datetime.now()
        duration = (end - start).total_seconds()
        logger.info(
            f"Run completed at {end.strftime('%Y-%m-%d %H:%M:%S')} | Run time "
            f"{duration:.2f} seconds"
        )
    except Exception as e:
        end = datetime.datetime.now()
        duration = (end - start).total_seconds()
        logger.error(f"{e}\n{traceback.format_exc()}\n")
        logger.info(
            f"Run terminated at {end.strftime('%Y-%m-%d %H:%M:%S')} | Run time to "
            f"failure {duration:.2f} seconds"
        )
