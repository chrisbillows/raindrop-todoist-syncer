"""
Application configuration.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import dotenv_values


@dataclass(frozen=True)
class UserConfig:
    config_dir: Path
    env_file: Path
    # db_file:
    # metafile:
    todoist_api_key: str
    raindrop_client_id: str
    raindrop_client_secret: str
    raindrop_refresh_token: str
    raindrop_access_token: str


def make_user_config() -> UserConfig:
    config_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "rts"
    env_file = config_dir / ".env"
    # db_dir = config_dir / "rts.db"
    # metafile =
    env_vars = dotenv_values(env_file)
    return UserConfig(
        config_dir=config_dir,
        env_file=env_file,
        # db_dir=db_dir,
        # metafile=metafile,
        todoist_api_key=env_vars["TODOIST_API_KEY"],
        raindrop_client_id=env_vars["RAINDROP_CLIENT_ID"],
        raindrop_client_secret=env_vars["RAINDROP_CLIENT_SECRET"],
        raindrop_refresh_token=env_vars["RAINDROP_REFRESH_TOKEN"],
        raindrop_access_token=env_vars["RAINDROP_ACCESS_TOKEN"],
    )
