from raindrop import RaindropClient, RaindropsProcessor, Raindrop
from todoist import TodoistTaskCreator
from time import sleep


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
        print(f"Created task: {task.title}")


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
        print(f"RUN {count}".center(50, "-"))
        try:
            main()
            print("-" * 50)
            print()
            sleep(300)

        except Exception as e:
            import ipdb

            ipdb.post_mortem()


if __name__ == "__main__":
    run()
    