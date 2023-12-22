import json
from unittest.mock import patch, MagicMock

import pytest

from main import main
from raindrop import RaindropClient, RaindropsProcessor
from todoist import TodoistTaskCreator


@pytest.fixture
def mock_raindrops_data():
    with open("tests/mock_data/cumulative_rd_list.json") as f:
        return json.load(f)


@pytest.fixture
def mock_raindrop_client(mock_raindrops_data, monkeypatch):
    def mock_get_all_raindrops(self):
        return mock_raindrops_data
    monkeypatch.setattr(RaindropClient, "get_all_raindrops", mock_get_all_raindrops)


@pytest.fixture
def mock_raindrops_processor(monkeypatch):
    def mock_newly_favourited_raindrops_extractor(self):
        return []

    monkeypatch.setattr(
        RaindropsProcessor,
        "newly_favourited_raindrops_extractor",
        mock_newly_favourited_raindrops_extractor,
    )


@pytest.fixture
def mock_todoist_creator(monkeypatch):
    def mock_create_task(self, task):
        pass

    monkeypatch.setattr(TodoistTaskCreator, "create_task", mock_create_task)


class TestMain:

    def test_working_test(self):
        assert 1 == 1

    # def test_test_setup(
    #     self,
    #     mock_raindrop_client,
    #     mock_raindrops_processor,
    #     mock_todoist_creator,
    #     caplog,
    # ):
    #     """
    #     Run-through to test mocks and monkey patches work correctly.
    #     main has no return hence x = main() - if main runs it will return None

    #     There are three "outputs" from main:
    #     a) all_raindrops
    #     b) tasks_to_create
    #     c) task_creator

    #     I had hoped just to mock all_raindrops and task_creator - but tasks to create
    #     writes to the db at the moment!
    #     """
    #     x = main()
    #     assert x == None

    def test_invalid_token(
        self,
        mock_raindrop_client,
        mock_raindrops_processor,
        mock_todoist_creator,
        caplog,
    ):
        with patch("raindrop.RaindropOauthHandler.refresh_token_process_runner") as mock_refresh_token_runner, patch(
            "raindrop.RaindropClient.valid_token",
            return_value = False
        ) as mock_valid_token:
            main()
            mock_refresh_token_runner.assert_called_once()

    def test_valid_token(
        self,
        mock_raindrop_client,
        mock_raindrops_processor,
        mock_todoist_creator,
        caplog,
    ):
        with patch("raindrop.RaindropOauthHandler.refresh_token_process_runner") as mock_refresh_token_runner, patch(
            "raindrop.RaindropClient.valid_token",
            return_value = True
        ) as mock_valid_token:
            main()
            mock_refresh_token_runner.assert_not_called()
