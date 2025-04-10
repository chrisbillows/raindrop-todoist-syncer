from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from raindrop_todoist_syncer.config import UserConfig, SystemConfig, SecretsConfig


@pytest.mark.parametrize(
    "attr, expected_value",
    [
        ("user_dir", Path("mock_user_dir")),
        ("config_dir", Path("mock_user_dir/.config/rts")),
        ("env_file", Path("mock_user_dir/.config/rts/.env")),
        ("logs_dir", Path("mock_user_dir/.config/rts/logs")),
        ("database_dir", Path("mock_user_dir/.config/rts/db")),
        ("metafile_dir", Path("mock_user_dir/.config/rts/metafile")),
        ("metafile_path", Path("mock_user_dir/.config/rts/metafile/metafile.txt")),
        ("launch_agents_dir", Path("mock_user_dir/Library/LaunchAgents")),
    ],
)
def test_system_config_init(attr: str, expected_value: Path):
    mock_system_config = SystemConfig(Path("mock_user_dir"))
    assert getattr(mock_system_config, attr) == expected_value


@pytest.mark.parametrize(
    "attr, expected_value",
    [
        ("todoist_api_key", "ab12"),
        ("raindrop_client_id", "cd34"),
        ("raindrop_client_secret", "ef56"),
        ("raindrop_refresh_token", "gh67"),
        ("raindrop_access_token", "ij910"),
    ],
)
def test_secrets_config_init_env_present_all_required_values_present(
    attr: str, expected_value: str, tmp_path: Path
):
    mock_user_dir = tmp_path / "mock_user_dir"
    mock_system_config = SystemConfig(mock_user_dir)

    mock_secrets = {
        "TODOIST_API_KEY": "ab12",
        "RAINDROP_CLIENT_ID": "cd34",
        "RAINDROP_CLIENT_SECRET": "ef56",
        "RAINDROP_REFRESH_TOKEN": "gh67",
        "RAINDROP_ACCESS_TOKEN": "ij910",
    }
    mock_secrets_str = "\n".join([f"{k} = '{v}'" for k, v in mock_secrets.items()])

    mock_system_config.env_file.parent.mkdir(parents=True, exist_ok=True)
    mock_system_config.env_file.write_text(mock_secrets_str)

    mock_secrets_config = SecretsConfig(mock_system_config)

    assert getattr(mock_secrets_config, attr) == expected_value


def test_secrets_config_init_env_present_value_missing(tmp_path: Path):
    mock_user_dir = tmp_path / "mock_user_dir"
    mock_system_config = SystemConfig(mock_user_dir)

    mock_secrets = {
        "TODOIST_API_KEY": "ab12",
        "RAINDROP_CLIENT_ID": "cd34",
        "RAINDROP_CLIENT_SECRET": "ef56",
        "RAINDROP_REFRESH_TOKEN": "gh67",
        # "RAINDROP_ACCESS_TOKEN": "ij910",  # Missing value
    }
    mock_secrets_str = "\n".join([f"{k} = '{v}'" for k, v in mock_secrets.items()])

    mock_system_config.env_file.parent.mkdir(parents=True, exist_ok=True)
    mock_system_config.env_file.write_text(mock_secrets_str)
    with pytest.raises(KeyError):
        SecretsConfig(mock_system_config)


def test_secrets_config_missing_env():
    mock_system_config = SystemConfig(Path("mock_user_dir"))
    with pytest.raises(FileNotFoundError):
        SecretsConfig(mock_system_config)


@pytest.mark.parametrize(
    "attr, expected_value",
    [
        ("user_dir", Path("mock_user_dir")),
        ("config_dir", Path("mock_user_dir/.config/rts")),
        ("env_file", Path("mock_user_dir/.config/rts/.env")),
        ("logs_dir", Path("mock_user_dir/.config/rts/logs")),
        ("database_dir", Path("mock_user_dir/.config/rts/db")),
        ("metafile_dir", Path("mock_user_dir/.config/rts/metafile")),
        ("metafile_path", Path("mock_user_dir/.config/rts/metafile/metafile.txt")),
        ("launch_agents_dir", Path("mock_user_dir/Library/LaunchAgents")),
        ("todoist_api_key", "ab12"),
        ("raindrop_client_id", "cd34"),
        ("raindrop_client_secret", "ef56"),
        ("raindrop_refresh_token", "gh78"),
        ("raindrop_access_token", "ij910"),
    ],
)
@patch("raindrop_todoist_syncer.config.dotenv_values")
@patch("raindrop_todoist_syncer.config.Path.exists", return_value=True)
def test_user_config(
    _mock_path_exists: MagicMock,
    mock_dotenv_values: MagicMock,
    attr: str,
    expected_value: str,
):
    # This test could use the `mock_user_config` confest fixture. This test doesn't
    # use a real path for `mock_user_dir`, so kept for this negligible difference.
    mock_dotenv_values.return_value = {
        "TODOIST_API_KEY": "ab12",
        "RAINDROP_CLIENT_ID": "cd34",
        "RAINDROP_CLIENT_SECRET": "ef56",
        "RAINDROP_REFRESH_TOKEN": "gh78",
        "RAINDROP_ACCESS_TOKEN": "ij910",
    }
    mock_system_config = SystemConfig(Path("mock_user_dir"))
    mock_secrets_config = SecretsConfig(mock_system_config)
    mock_user_config = UserConfig(mock_system_config, mock_secrets_config)

    assert getattr(mock_user_config, attr) == expected_value
