import argparse
import sys
from unittest.mock import patch, Mock, MagicMock

import pytest

from raindrop_todoist_syncer.config import SystemConfig, UserConfig
from raindrop_todoist_syncer.main import (
    main,
    driver,
    parse_args,
    fetch_raindrops_and_create_tasks,
)
from raindrop_todoist_syncer.rd_object import Raindrop


@patch("raindrop_todoist_syncer.main.TodoistTaskCreator.create_task")
@patch(
    "raindrop_todoist_syncer.main.RaindropsProcessor.newly_favourited_raindrops_extractor"
)
def test_fetch_raindrops_and_create_tasks(
    mock_rd_processor_rd_extractor: MagicMock,
    mock_todoist_task_creator_create_task: MagicMock,
    raindrop_object: Raindrop,
):
    mock_user_config = Mock()
    mock_rd_client = Mock()
    mock_db_manager = Mock()
    mock_rd_processor_rd_extractor.return_value = [raindrop_object]

    fetch_raindrops_and_create_tasks(mock_user_config, mock_rd_client, mock_db_manager)

    mock_rd_client.get_all_raindrops.assert_called_once()
    mock_rd_processor_rd_extractor.assert_called_once()
    mock_todoist_task_creator_create_task.assert_called_once()
    mock_db_manager.update_database.assert_called_once()


# Patch as __init_ calls API to refresh token. DBManager not mocked as passed to a Mock.
@patch("raindrop_todoist_syncer.main.RaindropClient")
@patch("raindrop_todoist_syncer.main.fetch_raindrops_and_create_tasks")
def test_driver_command_run(
    mock_fetch_raindrops_and_create_tasks: MagicMock,
    _mock_raindrop_client: MagicMock,
    mock_user_config: UserConfig,
):
    # No command, i.e. the default command creates the same Namespace object.
    mock_args = argparse.Namespace(command="run")
    driver(mock_args, mock_user_config)
    mock_fetch_raindrops_and_create_tasks.assert_called_once()


@patch(
    "raindrop_todoist_syncer.main.AutomationManager."
    "activate_automatic_rd_fetch_and_task_creation"
)
def test_driver_command_automate_enable(
    mock_activate_automate: MagicMock,
    mock_user_config: UserConfig,
):
    mock_args = argparse.Namespace(command="automate_enable")
    driver(mock_args, mock_user_config)
    mock_activate_automate.assert_called_once()


@patch(
    "raindrop_todoist_syncer.main.AutomationManager.deactivate_automatic_rd_fetch_and_task_creation"
)
def test_driver_command_run_automate_disable(
    mock_deactivate_automate: MagicMock,
    mock_user_config: UserConfig,
):
    mock_args = argparse.Namespace(command="automate_disable")
    driver(mock_args, mock_user_config)
    mock_deactivate_automate.assert_called_once()


@pytest.mark.parametrize(
    "command_ran_in_cli, expected",
    [
        ([], argparse.Namespace(command="run")),  # Test default argument is 'run'
        (["run"], argparse.Namespace(command="run")),
        (["automate_enable"], argparse.Namespace(command="automate_enable")),
        (["automate_disable"], argparse.Namespace(command="automate_disable")),
    ],
)
def test_parse_args(command_ran_in_cli: str | None, expected: argparse.Namespace):
    sys.argv = ["application"]
    sys.argv.extend(command_ran_in_cli)
    actual = parse_args()
    assert actual == expected


@patch("raindrop_todoist_syncer.main.driver")
@patch("raindrop_todoist_syncer.main.UserConfig.from_env_file")
@patch("raindrop_todoist_syncer.main.SystemConfig")
@patch("raindrop_todoist_syncer.main.parse_args")
def test_main(
    mock_parse_args: MagicMock,
    mock_system_config: MagicMock,
    mock_user_config_from_env: MagicMock,
    mock_driver: MagicMock,
    mock_system_config_real_paths: SystemConfig,
):
    # Real paths used as `configure_logging` will creates log dir.
    mock_system_config.return_value = mock_system_config_real_paths
    main()
    mock_parse_args.assert_called_once()
    mock_user_config_from_env.assert_called_once_with(mock_system_config_real_paths)
    mock_driver.assert_called_once()
