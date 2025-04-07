"""
Application configuration.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import dotenv_values


@dataclass
class UserConfig:
    """
    User configuration.
    """

    config_dir: Path
    env_file: Path
    database_directory: str
    metafile_directory: str
    metafile_path: str
    todoist_api_key: str
    raindrop_client_id: str
    raindrop_client_secret: str
    raindrop_refresh_token: str
    raindrop_access_token: str


def make_user_config() -> UserConfig:
    """
    Create a user config.

    Returns
    -------
    UserConfig
        An initialised UserConfig
    """
    config_dir = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "rts"
    env_file = config_dir / ".env"
    database_directory = config_dir / "rts.db"
    metafile_directory = config_dir / "metafile"
    metafile_path = metafile_directory / "metafile.txt"
    env_vars = dotenv_values(env_file)
    return UserConfig(
        config_dir=config_dir,
        env_file=env_file,
        database_directory=database_directory,
        metafile_directory=metafile_directory,
        metafile_path=metafile_path,
        todoist_api_key=env_vars["TODOIST_API_KEY"],
        raindrop_client_id=env_vars["RAINDROP_CLIENT_ID"],
        raindrop_client_secret=env_vars["RAINDROP_CLIENT_SECRET"],
        raindrop_refresh_token=env_vars["RAINDROP_REFRESH_TOKEN"],
        raindrop_access_token=env_vars["RAINDROP_ACCESS_TOKEN"],
    )
