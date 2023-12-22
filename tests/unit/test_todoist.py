import json
from unittest import mock
from unittest.mock import patch

import pytest

from raindrop import RaindropsProcessor
from todoist import TodoistTaskCreatorDev

@pytest.fixture
def todoist_task_creator():
    return TodoistTaskCreatorDev()

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
    
    def test_create_task_actual_rd_objects(self, todoist_task_creator, list_of_rd_objects):
        rd_object = list_of_rd_objects[2]
       
        with patch('todoist.TodoistAPI.add_task') as mock_add_task:
            todoist_task_creator.create_task(rd_object)
            mock_add_task.assert_called_once_with(
                content='**Obsidian - Sharpen your thinking**',
                project_id=TodoistTaskCreatorDev.MAIN_WORK_PROJECT,
                description='',
                due_string='today',
                due_lang='en',
                priority=1,
                labels=['Raindrop']
                )
            
        


