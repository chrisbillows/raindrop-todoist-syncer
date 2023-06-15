import os

from dotenv import load_dotenv
from todoist_api_python.api import TodoistAPI

from raindrop import Raindrop

load_dotenv()


class TodoistTaskCreator:
    """
    A class to create Todoist tasks from a Raindrop object.

    Attributes
    ----------
    MAIN_WORK_PROJECT : str
        a formatted string to hold the main work project ID
    TODOIST_API_KEY : str
        a string representing the Todoist API key
    api : TodoistAPI
        an instance of the TodoistAPI class
    task_title : str
        a string representing the task title
    task_description : str
        a string representing the task description
    website_link : str
        a string representing the website link

    Methods
    -------
    create_task():
        Creates a new task in Todoist.
    _add_link_as_comment(task_id: str):
        Adds the Raindrops website link as a comment to the task.
    """

    MAIN_WORK_PROJECT = "2314091414"
    TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")

    def __init__(self, raindrop: Raindrop) -> None:
        """
        Constructs all the necessary attributes for the TodoistTaskCreator object.

        Parameters
        ----------
            raindrop : Raindrop
                an instance of the Raindrop class
        """

        self.api = TodoistAPI(self.TODOIST_API_KEY)
        self.task_title = raindrop.title
        self.task_description = raindrop.notes
        self.website_link = raindrop.link

    def create_task(self):
        """
        Creates a new task in Todoist.

        Returns
        -------
        None
        """

        try:
            task = self.api.add_task(
                content=f"**{self.task_title}**",
                project_id=self.MAIN_WORK_PROJECT,
                description=f"{self.task_description}",
                due_string="today",
                due_lang="en",
                priority=1,
                labels=["Raindrop"],
            )

            self._add_link_as_comment(task.id)

        except Exception as error:
            print(error)

    def _add_link_as_comment(self, task_id):
        """
        Adds the Raindrop's website link as a comment to the task. This is added as a
        comment and not to the description because Todoist renders a preview for links
        in the comments (not for all links).

        Parameters
        ----------
        task_id : str
            The id of the task

        Returns
        -------
        None
        """

        try:
            comment = self.api.add_comment(task_id=task_id, content=self.website_link)
        except Exception as error:
            print(error)
