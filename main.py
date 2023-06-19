import logging

from raindrop import RaindropClient, RaindropsProcessor, Raindrop
from todoist import TodoistTaskCreator
from time import sleep, time

logging.basicConfig(
    filename="log.log",
    level=logging.INFO,
    format="%(levelname)s (%(asctime)s): %(message)s (Line: %(lineno)d) [%(filename)s])",
    datefmt="%Y-%m-%dT%H:%M:%S",
    encoding="utf-8",
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

logging.getLogger().addHandler(console_handler)


def main():
    """
    Main function that does the following steps:
    - Get all raindrops from the RaindropClient.
    - Process these raindrops.
    - For each processed task, create a task in Todoist.
    """

    raindrop_client = RaindropClient()
    all_raindrops = raindrop_client.get_all_raindrops()

    raindrops_processor = RaindropsProcessor(all_raindrops)
    tasks_to_create = raindrops_processor.process_favourites()

    for task in tasks_to_create:
        task_creator = TodoistTaskCreator(task)
        task_creator.create_task()
        logging.info(f"Created task: {task.title}")


def run():
    """
    Function that runs the main function and handles exceptions.
    The main function will run for 4 hours (once every five minutes, a total of 480 
    passes)
        
    If an error occurs, the function enters post-mortem debugging.
    """

    count = 0

    while count < 481:
        
        count += 1
        logging.info(f"Commence run {count}")
        
        start_time = time() 
        
        try:
            main()
            logging.info(f"Run {count} completed")
            
            end_time = time()
            duration = end_time - start_time
            logging.info(f"Run {count} took {duration:.2f} seconds")
            
            sleep(300)

        except Exception as e:
            import ipdb

            ipdb.post_mortem()


if __name__ == "__main__":
    run()
