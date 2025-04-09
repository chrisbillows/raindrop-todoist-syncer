from pathlib import Path
import subprocess

from loguru import logger

from raindrop_todoist_syncer.config import UserConfig
from raindrop_todoist_syncer.logging_config import configure_logging

configure_logging()

PLIST_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
        <key>Label</key>
        <string>com.raindrop-todoist-syncer.raindrop_fetcher</string>

        <key>ProgramArguments</key>
        <array>
                <string>{{PATH_TO_EXECUTABLE}}</string>
        </array>

        <key>RunAtLoad</key>
        <true/>

        <key>StandardOutPath</key>
        <string>{{PATH_TO_LOGS_DIR}}/launchd-stdout.log</string>

        <key>StandardErrorPath</key>
        <string>{{PATH_TO_LOGS_DIR}}/launchd-stderr.log</string>
</dict>
</plist>
"""


class AutomationManager:
    """
    Class to enable/disable automated raindrop fetch/task creation.

    Assumes raindrop-todoist-syncer has been installed via pipx or uvx and the 'rts'
    entry point command is globally available in the user.

    Methods
    -------
    activate_automatic_rd_fetch_and_task_creation
        Public driver method to activate RTS automation.

    deactivate_automatic_rd_fetch_and_task_creation
        Public driver method to deactivate RTS automation.
    """

    def __init__(self, user_config: UserConfig):
        """
        Initialise object.

        Parameters
        ----------
        user_config:
            A user config object.
        """
        self.user_config = user_config
        self.path_to_rts_executable = (
            self.user_config.user_dir / ".local" / "bin" / "rts"
        )
        self.automation_dir = self.user_config.config_dir / "automation"
        self.plist_file_path = (
            self.automation_dir / "com.raindrop-todoist-syncer.raindrop_fetcher.plist"
        )
        self.plist_content = ""
        self.launch_agents_dir = user_config.user_dir / "Library" / "LaunchAgents"
        self.symlink_path = self.launch_agents_dir / self.plist_file_path.name

    def activate_automatic_rd_fetch_and_task_creation(self) -> None:
        """
        Public driver method to activate RTS automation.
        """
        self._ensure_directories_exist()
        self._create_plist_file_content()
        self._write_plist_file()
        self._verify_plist_file()
        self._create_symlink_in_launch_agents_dir()
        self._install_plist_file()
        logger.info(
            f"Raindrop Todoist Syncer is now installed to run automatically. To confirm"
            f" check log files at:\n{self.user_config.logs_dir}"
        )

    def deactivate_automatic_rd_fetch_and_task_creation(self) -> None:
        """
        Public driver method to deactivate RTS automation.
        """
        self._uninstall_plist_file()
        self._delete_files()
        logger.info("Raindrop Todoist Syncer will no longer auto fetch your Raindrops")

    def _ensure_directories_exist(self):
        """
        Ensure directories required for plist operations exist.

        This includes:
        - The automation directory for storing the plist
        - The logs directory for stdout/stderr defined in the plist
        - The LaunchAgents directory for symlink placement (this will very likely
          already exist and is therefore a double check)
        """
        self.automation_dir.mkdir(parents=True, exist_ok=True)
        self.user_config.logs_dir.mkdir(parents=True, exist_ok=True)
        self.user_config.launch_agents_dir.mkdir(parents=True, exist_ok=True)

    def _create_plist_file_content(self) -> None:
        """
        Create plist file content as object attribute `self.plist_content`.

        Replaces plist template  `{{PLACEHOLDERS}}` with required details.
        """
        content = PLIST_TEMPLATE
        content = content.replace(
            "{{PATH_TO_EXECUTABLE}}", str(self.path_to_rts_executable)
        )
        content = content.replace(
            "{{PATH_TO_LOGS_DIR}}",
            str(self.user_config.logs_dir),
        )
        logger.debug("Generated plist file content.")
        self.plist_content = content

    def _write_plist_file(self) -> None:
        """
        Write the plist file with content to the plist file path.
        """
        self.plist_file_path.parent.mkdir(exist_ok=True)
        self.plist_file_path.write_text(self.plist_content)
        logger.info(f"Plist file created at {self.plist_file_path}")

    def _verify_plist_file(self) -> None:
        """
        Use macOS `plutil` to verify the content of the plist file is valid.
        """
        try:
            self._run_command_line_tool("plutil", "-lint", self.plist_file_path)
            logger.info("Plist file verified by plutil")
        except subprocess.CalledProcessError as err:
            logger.error(
                "Uh-oh. Raindrop Todoist Syncer has created an invalid plist file. "
                "We're sorry! `rts automate` will not be available until we fix this. "
                "Please raise an issue on GitHub:"
                "https://github.com/chrisbillows/raindrop-todoist-syncer/issues. Please"
                " include the below:"
            )
            logger.error(f"return code: {err.returncode}")
            logger.error(f"output: {err.output}")
            logger.error(f"stdout: {err.stdout}")
            logger.error(f"stderr {err.stderr}")
            raise err

    def _create_symlink_in_launch_agents_dir(self) -> None:
        """
        Create a symlink to the plist file in the user launch agents dir.
        """
        # Because I can never remember the order: `symlink_file.symlink_to(source_file)`
        self.symlink_path.symlink_to(self.plist_file_path)
        logger.info(f"Symlink created at {self.symlink_path}")

    def _install_plist_file(self) -> None:
        """
        Load the symlink plist into launchctl.
        """
        self._run_command_line_tool("launchctl", "load", self.symlink_path)
        logger.info("Plist file installed")

    def _uninstall_plist_file(self) -> None:
        """
        Unload the symlink plist from launchctl.
        """
        self._run_command_line_tool("launchctl", "unload", self.symlink_path)
        logger.info("Plist un-installed")

    def _delete_files(self):
        """
        Delete files ready for clean re-install. Saves having to check existence etc.

        NOTE: No need to delete the plist file itself - pathlib will overwrite it anyway.

        """
        self.symlink_path.unlink()

    def _run_command_line_tool(self, tool: str, command: str, file: Path):
        """
        Run CLI commands on a file.

        Raises
        ------
        subprocess.CalledProcessError
            Raised if the given command does not return a 0 status code.
        """
        try:
            subprocess.run(
                [tool, command, str(file)],
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info(f"Ran '{tool} {command} {file}'")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running '{tool} {command}' for plist file: {file}")
            raise e
