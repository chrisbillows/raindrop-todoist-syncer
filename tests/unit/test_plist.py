from pathlib import Path
import subprocess
import sys
from unittest.mock import patch, MagicMock
from contextlib import ExitStack

import pytest

from raindrop_todoist_syncer.config import UserConfig
from raindrop_todoist_syncer.plist import AutomationManager


@pytest.fixture
def mock_automation_manager(mock_user_config):
    return AutomationManager(mock_user_config)


@pytest.fixture
def mock_plist_file_content():
    mock_content = """
        <plist version="1.0">
        <dict>
            <key>Label</key>
                <string>mock</string>
    """
    return mock_content


@pytest.mark.parametrize(
    "attr", ["path_to_rts_executable", "automation_dir", "plist_file_path"]
)
def test_mock_automation_manager_path_attributes_do_not_use_real_user_dir(
    mock_automation_manager: AutomationManager, attr: str
):
    actual = str(getattr(mock_automation_manager, attr))
    assert str(Path.home()) not in actual


def test_mock_automation_manager_assert_logs_in_plist_content_are_not_real_user_dir(
    mock_automation_manager: AutomationManager,
):
    real_user_dir = str(Path.home())
    mock_automation_manager._create_plist_file_content()
    actual = mock_automation_manager.plist_content
    assert real_user_dir not in actual[17]
    assert real_user_dir not in actual[20]


ACTIVATE_METHODS = [
    "_ensure_directories_exist",
    "_create_plist_file_content",
    "_write_plist_file",
    "_verify_plist_file",
    "_create_symlink_in_launch_agents_dir",
    "_install_plist_file",
]


# All methods must be patched to prevent real method calls from executing. Each test
# case checks whether one specific method was called.
@pytest.mark.parametrize("method_to_check", ACTIVATE_METHODS)
def test_activate_automatic_calls_each_method_once(
    method_to_check: str, mock_user_config: UserConfig
):
    # Create unittest.mock._patch objects for each method in METHODS.
    patches = {name: patch.object(AutomationManager, name) for name in ACTIVATE_METHODS}

    # Use ExitStack to enter multiple, dynamically generated context managers. This
    # replaces the need for multiple `with patch(...) as mock:` lines.
    with ExitStack() as stack:
        # Activate each _patch object using the context manager. The context manager
        # calls _patch.__enter__() and __exit__(), which wrap _patch.start() and
        # _patch.stop(). _patch.start() activates the _patch object, replacing the real
        # method with a MagicMock. Collect the resulting MagicMock objects in a dict for
        # dynamic referencing in the assert.
        mocks = {name: stack.enter_context(patch_) for name, patch_ in patches.items()}
        am = AutomationManager(mock_user_config)
        am.activate_automatic_rd_fetch_and_task_creation()

    mocks[method_to_check].assert_called_once()


DEACTIVATE_METHODS = ["_uninstall_plist_file", "_delete_files"]


# All methods must be patched to prevent real method calls from executing. Each test
# case checks whether one specific method was called.
@pytest.mark.parametrize("method_to_check", DEACTIVATE_METHODS)
def test_deactivate_automatic_calls_each_method_once(
    method_to_check: str, mock_user_config: UserConfig
):
    # Create unittest.mock._patch objects for each method in METHODS.
    patches = {
        name: patch.object(AutomationManager, name) for name in DEACTIVATE_METHODS
    }

    # Use ExitStack to enter multiple, dynamically generated context managers. This
    # replaces the need for multiple `with patch(...) as mock:` lines.
    with ExitStack() as stack:
        # Activate each _patch object using the context manager. The context manager
        # calls _patch.__enter__() and __exit__(), which wrap _patch.start() and
        # _patch.stop(). _patch.start() activates the _patch object, replacing the real
        # method with a MagicMock. Collect the resulting MagicMock objects in a dict for
        # dynamic referencing in the assert.
        mocks = {name: stack.enter_context(patch_) for name, patch_ in patches.items()}
        am = AutomationManager(mock_user_config)
        am.deactivate_automatic_rd_fetch_and_task_creation()

    mocks[method_to_check].assert_called_once()


def test_automation_manager_ensure_directories_exist(
    mock_automation_manager: AutomationManager,
):
    mock_automation_manager._ensure_directories_exist()
    assert mock_automation_manager.automation_dir.exists()
    assert mock_automation_manager.user_config.launch_agents_dir.exists()
    logs_dir = mock_automation_manager.user_config.config_dir / "logs"
    assert logs_dir.exists()


def test_create_plist_file_content(mock_automation_manager: AutomationManager):
    mock_automation_manager._create_plist_file_content()
    actual = mock_automation_manager.plist_content.split("\n")
    executable = actual[10].strip()
    stdout_log = actual[17].strip()
    stderr_log = actual[20].strip()

    assert executable.endswith(".local/bin/rts</string>")
    assert stdout_log.endswith("/config_dir/logs/launchd-stdout.log</string>")
    assert stderr_log.endswith("/config_dir/logs/launchd-stderr.log</string>")
    assert actual[21] == "</dict>"
    assert actual[22] == "</plist>"


def test_write_plist_file(
    mock_automation_manager: AutomationManager, mock_plist_file_content: str
):
    # Create the plist file directory
    mock_automation_manager._ensure_directories_exist()

    mock_automation_manager.plist_content = mock_plist_file_content
    mock_automation_manager._write_plist_file()

    with open(mock_automation_manager.plist_file_path, "r") as file_handle:
        content = file_handle.readlines()

    assert content[1].strip() == '<plist version="1.0">'
    assert content[4].strip() == "<string>mock</string>"
    assert len(content) == 6


@pytest.mark.skipif(
    sys.platform != "darwin", reason="Only runs on macOS so skip for CI"
)
def test_verify_plist_content_for_valid_content(
    mock_automation_manager: AutomationManager,
):
    # This is a bit of a naughty test. It uses the plutil to validate the content
    # we make. Ergo it couples a) the content being valid b) the verification call
    # being made correctly.
    mock_automation_manager._ensure_directories_exist()
    mock_automation_manager._create_plist_file_content()
    mock_automation_manager._write_plist_file()
    actual = mock_automation_manager._verify_plist_file()
    assert actual is None


@pytest.mark.skipif(
    sys.platform != "darwin", reason="Only runs on macOS so skip for CI"
)
def test_verify_plist_file_content_for_invalid_content(
    mock_automation_manager: AutomationManager, mock_plist_file_content: str
):
    # Create plist directory, add mock content to object and write plist file. Yes,
    # these tests are more coupled than love island... Sorry future, Chris!
    mock_automation_manager._ensure_directories_exist()
    mock_automation_manager.plist_content = mock_plist_file_content
    mock_automation_manager._write_plist_file()

    with pytest.raises(
        subprocess.CalledProcessError, match="returned non-zero exit status 1."
    ):
        mock_automation_manager._verify_plist_file()


def test_create_symlink_in_launch_agents_dir(
    mock_automation_manager: AutomationManager, mock_plist_file_content: str
):
    # Create the plist file directory
    mock_automation_manager._ensure_directories_exist()
    # Add plist file content to the object
    mock_automation_manager.plist_content = mock_plist_file_content
    # Create the plist file
    mock_automation_manager._write_plist_file()

    mock_automation_manager._create_symlink_in_launch_agents_dir()

    assert mock_automation_manager.symlink_path.exists()


@patch("raindrop_todoist_syncer.plist.AutomationManager._run_command_line_tool")
def test_install_plist_file(
    mock_run_command_line_tool: MagicMock,
    mock_automation_manager: AutomationManager,
):
    mock_automation_manager._install_plist_file()
    mock_run_command_line_tool.assert_called_once_with(
        "launchctl", "load", mock_automation_manager.symlink_path
    )


@patch("raindrop_todoist_syncer.plist.AutomationManager._run_command_line_tool")
def test_uninstall_plist_file(
    mock_run_command_line_tool: MagicMock,
    mock_automation_manager: AutomationManager,
):
    mock_automation_manager._uninstall_plist_file()
    mock_run_command_line_tool.assert_called_once_with(
        "launchctl", "unload", mock_automation_manager.symlink_path
    )


@patch("raindrop_todoist_syncer.plist.Path.unlink")
def test_delete_files_unlinks_symlink(
    mock_pathlib_unlink: MagicMock,
    mock_automation_manager: AutomationManager,
):
    mock_automation_manager._delete_files()
    mock_pathlib_unlink.assert_called_once()


@patch("raindrop_todoist_syncer.plist.subprocess.run")
def test_run_command_line_tool(
    mock_subprocess: MagicMock,
    mock_automation_manager: AutomationManager,
):
    mock_automation_manager._run_command_line_tool("fake-tool", "run-forrest", "cath")
    mock_subprocess.assert_called_once_with(
        ["fake-tool", "run-forrest", "cath"], check=True, capture_output=True, text=True
    )
