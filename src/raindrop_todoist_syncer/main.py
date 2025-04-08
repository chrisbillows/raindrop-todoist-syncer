import argparse
import datetime
import traceback
from loguru import logger

from raindrop_todoist_syncer.config import UserConfig, make_user_config
from raindrop_todoist_syncer.db_manage import DatabaseManager
from raindrop_todoist_syncer.plist import AutomationManager
from raindrop_todoist_syncer.rd_process import RaindropsProcessor
from raindrop_todoist_syncer.rd_client import RaindropClient
from raindrop_todoist_syncer.td_task import TodoistTaskCreator

from raindrop_todoist_syncer.logging_config import configure_logging

configure_logging()


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


def fetch_raindrops_and_create_tasks() -> None:
    """
    Fetch raindrops, create tasks and update database.
    """
    user_config: UserConfig = make_user_config()
    logger.info(user_config)
    rc = RaindropClient(user_config)
    dbm = DatabaseManager(user_config)
    all_raindrops = rc.get_all_raindrops()
    rp = RaindropsProcessor(user_config, all_raindrops)
    tasks_to_create = rp.newly_favourited_raindrops_extractor()
    for task in tasks_to_create:
        task_creator = TodoistTaskCreator(user_config, task)
        task_creator.create_task()
        dbm.update_database([task])


def driver(args: argparse.Namespace):
    """
    Driver function.

    Parameters
    ----------
    args: argparse.Namespace
        The parsed args

    """
    logger.info(f"Parsed args were {args}")

    if args.command == "run":
        fetch_raindrops_and_create_tasks()

    if args.command == "automate_enable":
        user_config = make_user_config()
        am = AutomationManager(user_config)
        am.activate_automatic_rd_fetch_and_task_creation()

    elif args.command == "automate_disable":
        user_config = make_user_config()
        am = AutomationManager(user_config)
        am.deactivate_automatic_rd_fetch_and_task_creation


def main():
    """
    Entry point for raindrop todoist syncer.
    """
    args = parse_args()
    driver(args)


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
