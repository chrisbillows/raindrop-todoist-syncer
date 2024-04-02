import shutil

from loguru import logger


class ExistingTokenError(Exception):
    pass


class DuplicateAccessTokenError(Exception):
    pass


class EnvDataOverwriteError(Exception):
    pass


class AccessTokenNotWrittenError(Exception):
    pass


class EnvironmentVariablesFileManager:
    """A class to mange the contents of .env file.

    This class manages the contents of the .env file itself. It contains methods that
    allow for refresh

    Attributes
    ----------
    env_file: default = "env"
        Path to a .env file that can will be read into memory and overwritten.

    NOTE
    ----
    `env_file` is not read into the environment here. This is for updating the file,
    and allows for passing different .env files for testing.
    """

    def __init__(self, env_file=".env", env_backup=".env.backup") -> None:
        self.env_file = env_file
        self.env_backup = env_backup

    def write_new_access_token(self, access_token: str) -> None:
        new_env_body = self._create_env_body_with_updated_access_token(access_token)
        validated_new_body = self._new_env_validator(new_env_body)
        self._write_new_body_to_env(validated_new_body)
        logger.info(
            f"Success! Access token refreshed - {access_token} written to .env."
        )

    def _create_env_body_with_updated_access_token(self, access_token: str) -> list:
        """Recreates the existing .env body including a newly extracted access token.

        1) Uses the new access token to creates a full line, with correct .env format.
        2) Reads the current .env into memory.
        3) Checks if a line already begins RAINDROP_ACCESS_TOKEN.
        4) If so, it targets that line and overwrites it with the new access token line.
        5) If not, it adds the new_line to the end of the body.

        Parameters
        ----------
        access_token: str
            An extracted Raindrop access token from an oauth response. This response
            will be the same for an oauth request of either grant_type
            (authorization_code or refresh_token).
            #TODO: This method needs to be generalized for both token types.

        Returns
        -------
        lines: list
               The previous .env body as a list, with the new access token included
               (either overwriting the previous token, or inserted at the end.)
        """
        new_line = f"RAINDROP_ACCESS_TOKEN = '{access_token}'\n"
        target_line = None

        with open(self.env_file, "r") as file:
            lines = file.readlines()

        for idx, line in enumerate(lines):
            if line.startswith("RAINDROP_ACCESS_TOKEN"):
                target_line = idx
                break

        if target_line is not None:
            lines[target_line] = new_line
        else:
            lines.append(new_line)

        return lines

    def _new_env_validator(self, new_body: list) -> list:
        """Runs simple validation checks on a new .env body.

        See inline comments for specific checks.

        Known edge cases that will pass:
        - where a line was inserted in error AND a line was deleted in error would pass.
        - where a line is added in an overwrite situation
            (i.e. the fact it doesn't distinguish between an `overwrite` where lines
            stay the same vs. `no existing access` where lines increase by one).
        - where an existing token is deleted

        #TODO: Raised issue #6. Using length to validate the body may not work. It may
            be simpler to handle .env bodies with/without a previous access token
            seperately. Or to do a more involved check e.g. extract all tokens from the
            old and new .envs into dicts and compare one-by-one.

        Parameters
        -----------
        new_body : list
            The potential new body content for the .env file.

        Returns
        -------
        new_body : list
            The now validated body content for the .env file.

        Raises:
        -------
        DuplicateAccessTokenError
            If the new_body contains duplicate tokens.
        EnvDataOverwriteError
            If the new_body is longer or shorter than expected, suggesting a failure in
            the new_body creation logic.
        """
        with open(self.env_file, "r") as file:
            lines = file.readlines()

        # Check env has changed
        if new_body == lines:
            raise EnvDataOverwriteError

        # Check has changed by none (overwrite) or one line only.
        length_difference = abs(len(new_body) - len(lines))

        if length_difference > 1:
            raise EnvDataOverwriteError

        access_tokens = []
        for line in new_body:
            if line.startswith("RAINDROP_ACCESS"):
                access_tokens.append(line)

        # Checks an access token is present
        if len(access_tokens) == 0:
            raise AccessTokenNotWrittenError

        # Checks no more than one access token is present
        if len(access_tokens) > 1:
            raise DuplicateAccessTokenError

        return new_body

    def _write_new_body_to_env(self, validated_new_body: list) -> bool:
        """Uses the new env_body to the overwrite the existing .env file.

        Backs up the existing .env to .env.backup. Then overwrites the .env file with
        the updated and validated new body - including the new access code.

        Parameters:
        -----------
        validated_new_body: list
            The newly updated, newly validated content for the .env.

        Returns:
        --------
        True: bool
            Will error if write fails. So I am reliably informed.
        """
        shutil.copy(self.env_file, self.env_backup)
        with open(self.env_file, "w") as file:
            file.writelines(validated_new_body)
