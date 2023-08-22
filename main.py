import traceback
import time
from raindrop import RaindropClient, RaindropsProcessor
from todoist import TodoistTaskCreator
import logging

logging.basicConfig(
    filename="app.log", filemode="a", format="%(name)s - %(levelname)s - %(message)s"
)


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
            print(f"{runs} is not a valid integer. Please try again.")

    while True:
        try:
            wait_time = input("Enter the wait time between runs in seconds: ")
            wait_time = int(wait_time)
            break
        except ValueError:
            print(f"{wait_time} is not a valid integer. Please try again.")

    done = 0
    while done < runs:
        done += 1
        print(f"RUN {done}".center(50, "-"))
        print("-" * 50)
        print()
        try:
            main()
            time.sleep(wait_time)

        except Exception as e:
            print("ERROR. CODE WILL TRY AGAIN IF RUNS REMAINING. ELSE DEBUG WITH LOG.")
            now = time.localtime()
            logging.error(
                f"{e}\n"
                f"Run {done} of {runs} | Interval {wait_time}\n"
                f"Run time: {time.strftime('%Y-%m-%d %H:%M:%S', now)}\n"
                f"{traceback.format_exc()}\n"
            )
            if done < runs:
                time.sleep(wait_time)


if __name__ == "__main__":
    run()
