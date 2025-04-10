"""
Application configuration.
"""

from pathlib import Path
from typing import Protocol

from dotenv import dotenv_values
from loguru import logger


class UserConfigProtocol(Protocol):
    """
    Define dynamic object attributes for static type checking and autocomplete.

    NOTE: This can't be tested because there is no runtime enforcement.
    """

    user_dir = Path
    config_dir: Path
    env_file: Path
    logs_dir: Path
    database_directory: Path
    metafile_directory: Path
    metafile_path: Path
    launch_agents_dir: Path
    logs_dir: Path
    todoist_api_key: str
    raindrop_client_id: str
    raindrop_client_secret: str
    raindrop_refresh_token: str
    raindrop_access_token: str


class SystemConfig:
    """
    User's system configuration.

    Parameters
    ----------
    user_dir: Path, default = None
        Allow a directory to be passed as `user_dir` for testing.

    """

    def __init__(self, user_dir: Path | None = None) -> None:
        if user_dir is None:
            self.user_dir = Path.home()
        else:
            self.user_dir = user_dir
        self.config_dir = self.user_dir / ".config" / "rts"
        self.env_file = self.config_dir / ".env"
        self.logs_dir = self.config_dir / "logs"
        self.database_dir = self.config_dir / "db"
        self.metafile_dir = self.config_dir / "metafile"
        self.metafile_path = self.metafile_dir / "metafile.txt"
        self.launch_agents_dir = self.user_dir / "Library" / "LaunchAgents"


class SecretsConfig:
    """
    User's API secrets configuration.

    Parameters
    ----------
    system_dir: SystemConfig
        A system config object (required for the `.env` path).
    """

    def __init__(self, system_config: SystemConfig) -> None:
        self.system_config = system_config
        if not system_config.env_file.exists():
            logger.error(
                f"No '.env' file found at {self.system_config.env_file}. Please create "
                "this file to continue. See: "
                "https://github.com/chrisbillows/raindrop-todoist-syncer/blob/main/README.md"
            )
            raise FileNotFoundError

        env_vars = dotenv_values(system_config.env_file)

        try:
            self.todoist_api_key = env_vars["TODOIST_API_KEY"]
            self.raindrop_client_id = env_vars["RAINDROP_CLIENT_ID"]
            self.raindrop_client_secret = env_vars["RAINDROP_CLIENT_SECRET"]
            self.raindrop_refresh_token = env_vars["RAINDROP_REFRESH_TOKEN"]
            self.raindrop_access_token = env_vars["RAINDROP_ACCESS_TOKEN"]
        except KeyError as err:
            raise KeyError(f"Missing required environment variable: {err.args[0]}")


class UserConfig(UserConfigProtocol):
    """
    A User Config object.

    Combines SystemConfig and SecretsConfig objects

    """

    def __init__(
        self, system_config: SystemConfig, secrets_config: SecretsConfig
    ) -> None:
        self.system_config = system_config
        self.secrets_config = secrets_config
        self._promote_attributes(system_config)
        self._promote_attributes(secrets_config)

    def _promote_attributes(self, config_obj) -> None:
        for attr in vars(config_obj):
            setattr(self, attr, getattr(config_obj, attr))
