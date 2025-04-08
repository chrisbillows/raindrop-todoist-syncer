import argparse
import sys
from unittest.mock import patch, MagicMock

import pytest

from raindrop_todoist_syncer.main import main, driver, parse_args


@pytest.mark.parametrize(
    "command_ran_in_cli, expected",
    [
        ([], argparse.Namespace(command="run")),  # Test default argument is 'run'
        (["run"], argparse.Namespace(command="run")),
        (["automate_enable"], argparse.Namespace(command="automate_enable")),
        (["automate_disable"], argparse.Namespace(command="automate_disable")),
    ],
)
def test_parse_args_command_rts(
    command_ran_in_cli: str | None, expected: argparse.Namespace
):
    sys.argv = ["application"]
    sys.argv.extend(command_ran_in_cli)
    actual = parse_args()
    assert actual == expected


@patch("raindrop_todoist_syncer.main.fetch_raindrops_and_create_tasks")
def test_driver_command_run(mock_fetch_raindrops_and_create_tasks: MagicMock):
    # No command, i.e. the default command creates the same Namespace object.
    mock_args = argparse.Namespace(command="run")
    driver(mock_args)
    mock_fetch_raindrops_and_create_tasks.assert_called_once()


# @patch.object(AutomationManager, "activate_automatic_rd_fetch_and_task_creation")
# def test_driver_command_automate_enable(mock_activate_automate: MagicMock):
#     mock_args = argparse.Namespace(command='automate_enable')
#     driver(mock_args)
#     mock_activate_automate.assert_called_once()


# @patch()
# def test_driver_command_run_automate_disable(
#     mock_fetch_raindrops_and_create_tasks: MagicMock
#     ):
#     mock_args = argparse.Namespace(command='run')
#     driver(mock_args)
#     mock_fetch_raindrops_and_create_tasks.assert_called_once()


@patch("raindrop_todoist_syncer.main.parse_args")
@patch("raindrop_todoist_syncer.main.driver")
def test_main(mock_driver: MagicMock, mock_parse_args: MagicMock):
    main()
    mock_driver.assert_called_once()
    mock_parse_args.assert_called_once()
