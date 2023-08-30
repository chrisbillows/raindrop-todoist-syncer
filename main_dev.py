import argparse
import fcntl
import os
import time
import traceback

from loguru import logger
from requests import HTTPError

from raindrop import RaindropClient, RaindropsProcessor, ExistingTokenError, MissingRefreshTokenError, UserCancelledError
from todoist import TodoistTaskCreator

from logging_config import configure_logging

configure_logging()


def obtain_lock(lock_file_path: str):
    """
    Tries to obtain an advisory lock on a file located at `lock_file_path`.
    
    This uses `fcntl.flock()` to apply an exclusive, non-blocking lock on the file.
    If the lock cannot be obtained (another instance has the lock), this function 
    returns None. Otherwise, it returns the file descriptor of the lock file.
    
    NOTE: fcntl is Unix only.
    """
    lock_file = open(lock_file_path, 'w')
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except IOError:
        return None

def release_lock(lock_file):
    """
    Releases the lock on the file
    """
    fcntl.flock(lock_file, fcntl.LOCK_UN)
    lock_file.close()

def main() -> None:
    """
    Calls the main class methods to fetch rds and create tasks from new favourites.
    """
    rdc = RaindropClient()
    all_raindrops = rdc.get_all_raindrops()
    rp = RaindropsProcessor(all_raindrops)
    tasks_to_create = rp.newly_favourited_raindrops_extractor()
    tc = TodoistTaskCreator(tasks_to_create)
    tc.create_tasks()    

def runner(runs: int=1, interval: int=0) -> None:
    """
    A wrapper main() adding exception handling, logging and looping.
    
    Argparse takes two vars runs, interval to allow for continuous running of the 
    script in the terminal.  
    
    """
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
    try:
        lock_file = obtain_lock("/tmp/my_app.lock")
        if lock_file is None:
            logger.error("Another instance is already running. Exiting.")
            exit(1)
    except Exception as e:
        logger.error(f"Failed to obtain lock due to: {e}")
        exit(1)
    try: 
        parser = argparse.ArgumentParser(description="Run Raindrop to Todoist task creator.")
        parser.add_argument("--runs", type=int, help="Number of times to run", default=1)
        parser.add_argument("--interval", type=int, help="Interval between runs in seconds", default=60)
        args = parser.parse_args()
        # checks the environment variable - ensure this is set when setting up the cron job or else will always default to terminal.
        run_env = os.environ.get('MY_APP_ENV', 'terminal')  
        if run_env == 'cron':
            logger.info("Run via cron job")
        else:
            logger.info(f"Run via terminal | {args.runs} runs | {args.interval} interval")
        # call runner() with args taken by argparse or default values if no args passed 
        runner(args.runs, args.interval)
    finally:
        """
        Ensure release_lock is within a try/finally block to avoid leaving the file 
        locked.
        """
        try:
            release_lock(lock_file)
        except Exception as e:
            logger.error(f"Failed to release lock due to: {e}")

# logger.info(f"Collected {len(all_raindrops)} total bookmarks.")
# logger.info(f"Found {len(tasks_to_create)} tasks to create.")

