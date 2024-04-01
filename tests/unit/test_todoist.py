from unittest.mock import patch

import json
import pytest

from raindrop_todoist_syncer.rd_process import RaindropsProcessor
from raindrop_todoist_syncer.td_task_create import TodoistTaskCreator


@pytest.fixture
def todoist_task_creator(raindrop_object):
    return TodoistTaskCreator(raindrop_object)


@pytest.fixture
def list_of_rd_objects():
    """
    Create a list of three Raindrop objects.
    """
    with open("tests/mock_data/cumulative_rd_list.json", "r") as f:
        rds = json.load(f)
    rd_sample = rds[2:5]
    rdp = RaindropsProcessor(rd_sample)
    rd_objects = rdp._convert_to_rd_objects(rdp.all_rds)
    return rd_objects


class TestInit:
    def test_main_work_project(self, todoist_task_creator):
        assert todoist_task_creator.MAIN_WORK_PROJECT == "2314091414"

    def test_main_work_api_key(self, todoist_task_creator):
        assert todoist_task_creator.TODOIST_API_KEY is not None


class TestCreateTask:
    def test_create_task_actual_rd_objects(self, todoist_task_creator):
        with patch(
            "raindrop_todoist_syncer.td_task_create.TodoistAPI.add_task"
        ) as mock_add_task:
            todoist_task_creator.create_task()
            mock_add_task.assert_called_once_with(
                content="Welcome to Python.org",
                project_id=todoist_task_creator.MAIN_WORK_PROJECT,
                description="",
                due_string="today",
                due_lang="en",
                priority=1,
                labels=["Raindrop"],
            )
