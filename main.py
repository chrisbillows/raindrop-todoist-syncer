import datetime
import time
import traceback

from loguru import logger
from raindrop import RaindropClient, RaindropOauthHandler, RaindropsProcessor
from todoist import TodoistTaskCreator

from logging_config import configure_logging

configure_logging()


def main():
    """
    Main function that does the following steps:
    - Checks for a stale token and refreshes if necessary.
    - Get all raindrops from the RaindropClient.
    - Process these raindrops.
    - For each processed task, create a task in Todoist.
    """
    raindrop_client = RaindropClient()
    raindrop_oauth = RaindropOauthHandler()
    if raindrop_client.stale_token():
        logger.warning("Oauth token is stale.")
        logger.info("Attempting to refresh token.")
        raindrop_oauth.refresh_token_process_runner()    
    all_raindrops = raindrop_client.get_all_raindrops()
    logger.info(f"Collected {len(all_raindrops)} total bookmarks.")
    raindrops_processor = RaindropsProcessor(all_raindrops)
    tasks_to_create = raindrops_processor.newly_favourited_raindrops_extractor()
    logger.info(f"Found {len(tasks_to_create)} tasks to create.")
    for task in tasks_to_create:
        task_creator = TodoistTaskCreator(task)
        task_creator.create_task()
        logger.info(f"Created task: {task.title}")
    

def run():
    """
    Function that runs the main function and handles exceptions. Asks the user for:
    a) number of runs: [int]
    b) wait between runs in seconds [int]

    (Four hours = 480 runs)

    If an error occurs, currently caught and logged (in case of temporary issues with
    Raindrop or Todoist APIs, for example).
    """
    while True:
        try:
            runs = input("Enter the number of runs to complete: ")
            runs = int(runs)
            break
        except ValueError:
            logger.warning(f"{runs} is not a valid integer. Please try again.")

    while True:
        try:
            wait_time = input("Enter the wait time between runs in seconds: ")
            wait_time = int(wait_time)
            break
        except ValueError:
            logger.warning(f"{wait_time} is not a valid integer. Please try again.")

    logger.info(f"User selected {runs} runs and {wait_time} wait_time.")
    completed_runs = 0
    while completed_runs < runs:
        completed_runs += 1
        start = datetime.now()
        logger.info(f"Run {completed_runs}/{runs} started.")
        try:
            main()
            end_time = datetime.now() - start
            logger.info(
                f"Run {completed_runs}/{runs} completed in {end_time:.2f} seconds"
            )
            time.sleep(wait_time)

        except Exception as e:
            logger.error(f"{e}\n" f"{traceback.format_exc()}\n")
            if completed_runs < runs:
                logger.info(
                    f"ERROR. CODE WILL RE-TRY IN {wait_time} AGAIN. {runs - completed_runs} RUN ATTEMPTS REMAIN."
                )
                time.sleep(wait_time)


if __name__ == "__main__":
    #! run commented out for plist
    # TODO replace with argparse optionality
    # run()
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
