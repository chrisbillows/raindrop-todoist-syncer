from pathlib import Path

import pytest

from raindrop_todoist_syncer.config import UserConfig, SystemConfig, SecretsConfig
from tests.conftest import mock_env_vars_func


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
    "attr, expected_value", [(k.lower(), v) for k, v in mock_env_vars_func().items()]
)
def test_secrets_config_init_all_required_values_present(
    attr: str, expected_value: str
):
    mock_secrets_config = SecretsConfig(mock_env_vars_func())
    assert getattr(mock_secrets_config, attr) == expected_value


def test_secrets_config_init_value_missing():
    env_var = mock_env_vars_func()
    env_var.pop("RAINDROP_ACCESS_TOKEN")
    with pytest.raises(KeyError):
        SecretsConfig(env_var)


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
    ]
    + [(k.lower(), v) for k, v in mock_env_vars_func().items()],
)
def test_user_config_init_and_promote_attributes(attr: str, expected_value: str):
    # This test could use the `mock_user_config` confest fixture. This test doesn't
    # use a real path for `mock_user_dir`, so kept for that negligible difference.
    mock_system_config = SystemConfig(Path("mock_user_dir"))
    mock_secrets_config = SecretsConfig(mock_env_vars_func())
    mock_user_config = UserConfig(mock_system_config, mock_secrets_config)
    assert getattr(mock_user_config, attr) == expected_value


def test_user_config_from_env_file_happy_path(
    mock_system_config_real_paths: SystemConfig,
):
    mock_system_config_real_paths.env_file.parent.mkdir(parents=True, exist_ok=True)
    mock_system_config_real_paths.env_file.write_text(
        "\n".join([f"{k} = {v}" for k, v in mock_env_vars_func().items()])
    )

    user_config = UserConfig.from_env_file(mock_system_config_real_paths)
    assert isinstance(user_config, UserConfig)


def test_user_config_from_env_file_env_missing_key():
    system_config = SystemConfig(Path("mock_user_dir"))
    with pytest.raises(FileNotFoundError):
        UserConfig.from_env_file(system_config)


def test_user_config_from_env_file_missing_env_file():
    system_config = SystemConfig(Path("mock_user_dir"))
    with pytest.raises(FileNotFoundError):
        UserConfig.from_env_file(system_config)


# # @patch("raindrop_todoist_syncer.config.dotenv_values")
