import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from raindrop_todoist_syncer.config import UserConfig, make_user_config


@pytest.mark.parametrize(
    "attr, expected_value",
    [
        ("todoist_api_key", "ab12"),
        ("raindrop_client_id", "cd34"),
        ("raindrop_client_secret", "ef56"),
        ("raindrop_refresh_token", "gh78"),
        ("raindrop_access_token", "ij910"),
        ("config_dir", Path("mock_config_dir/rts")),
        ("env_file", Path("mock_config_dir/rts/.env")),
        # "db_dir" = config_dir / "rts.db")
        # "metafile" =
    ],
)
@patch.dict(os.environ, XDG_CONFIG_HOME="mock_config_dir")
@patch("raindrop_todoist_syncer.config.dotenv_values")
def test_make_user_config(
    mock_dotenv_values: MagicMock, attr: str, expected_value: str
):
    mock_dotenv_values.return_value = {
        "TODOIST_API_KEY": "ab12",
        "RAINDROP_CLIENT_ID": "cd34",
        "RAINDROP_CLIENT_SECRET": "ef56",
        "RAINDROP_REFRESH_TOKEN": "gh78",
        "RAINDROP_ACCESS_TOKEN": "ij910",
    }
    user_config: UserConfig = make_user_config()
    assert getattr(user_config, attr) == expected_value
