import argparse
import os
import time
import traceback

from loguru import logger
from requests import HTTPError

from raindrop import RaindropClient, RaindropsProcessor, ExistingTokenError, MissingRefreshTokenError, UserCancelledError
from todoist import TodoistTaskCreator

from logging_config import configure_logging

configure_logging()

def main() -> None:
    rdc = RaindropClient()
    all_raindrops = rdc.get_all_raindrops()
    rp = RaindropsProcessor(all_raindrops)
    tasks_to_create = rp.newly_favourited_raindrops_extractor()
    tc = TodoistTaskCreator(tasks_to_create)
    tc.create_tasks()    

def runner(runs: int=1, interval: int=0) -> None:
    for i in range(runs):
        try:
            start = time.time()
            main()
            end_time = time.time() - start
            logger.info("Run %s/%s completed in %.2f seconds", i+1, runs, end_time)
            time.sleep(interval)
        # TODO: Make custom exception for ValueError exceptions
        except (ValueError, HTTPError, ExistingTokenError, MissingRefreshTokenError, UserCancelledError) as e:
            logger.error(f"{e} | {traceback.format_exc()}\n")
            if i - 1 > 0:
                logger.info(f"ERROR. CODE WILL RETRY IN {interval} AGAIN. {i-1} RUN ATTEMPTS REMAIN.")
                time.sleep(interval)
            else:
                logger.info(f"ERROR. HOWEVER NO MORE RUNS REMAIN. RE-START PROGRAMME TO RETRY.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Raindrop to Todoist task creator.")
    parser.add_argument("--runs", type=int, help="Number of times to run", default=1)
    parser.add_argument("--interval", type=int, help="Interval between runs in seconds", default=60)
    
    args = parser.parse_args()
    run_env = os.environ.get('MY_APP_ENV', 'terminal')  
    if run_env == 'cron':
        logger.info("Run via cron job")
    else:
        logger.info(f"Run via terminal | {args.runs} runs | {args.interval} interval")
       
    runner(args.runs, args.interval)


# logger.info(f"Collected {len(all_raindrops)} total bookmarks.")
# logger.info(f"Found {len(tasks_to_create)} tasks to create.")

