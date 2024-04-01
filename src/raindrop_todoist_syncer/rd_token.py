from typing import Optional
import re
import warnings
import webbrowser

from loguru import logger
from urllib.parse import urlparse, parse_qs

from raindrop_todoist_syncer.rd_credentials import RaindropCredentialsManager
from raindrop_todoist_syncer.raindrop import EnvironmentVariablesFileManager


def unfinished_warning(message):
    warnings.warn(message, category=UserWarning, stacklevel=2)


class BadProgrammerError(Exception):
    pass


class MissingRefreshTokenError(Exception):
    pass


class UserCancelledError(Exception):
    pass


class RaindropAccessTokenRefresher:
    def __init__(
        self, rcm: RaindropCredentialsManager, evfm: EnvironmentVariablesFileManager
    ) -> None:
        """
        Initializes the refresher with an RaindropCredentialsManager for OAuth
        operations.
        """
        self.rcm = rcm
        if not rcm.RAINDROP_REFRESH_TOKEN:
            raise MissingRefreshTokenError("No refresh token in .env. Refresh aborted")
        self.evfm = evfm

    def refresh_token_process_runner(self) -> bool:
        """Runs the process to refresh a stale access token.

        This method uses a Raindrop Oauth2 refresh token to generate a new, valid oauth2
        access token.

        Using `raindrop_access_token_refresher`:
        1) Creates a valid request (header/body)

        Using `raindrop_credentials_manager`:

        2) Makes the request.
        3) Validates the response object
        4) Extracts the new access token from the response.

        Using `environment_variables_file_manager`:`
        4) Creates a new .env file body using the current .env body and overwriting the
            stale oauth token.
        5) Validates the new .env body then overwrites the old .env file.


        Raises
        ------
        MissingRefreshTokenError
            If no refresh token is present. This can be used to prevent the refresh
            process running and divert to a "authorization code" oauth request.

        Returns
        -------
        True
            Code should raise an error if the entire operation doesn't complete.
        """
        logger.info("Attempting to refresh token.")
        body = self._refresh_token_create_body()
        response = self.rcm.make_request(body)
        self.rcm.response_validator(response)
        access_token = self.rcm.extract_access_token(response)
        self.evfm.write_new_access_token(access_token)

    def _refresh_token_create_body(self) -> dict[str, str]:
        """
        Create body/data dict required to refresh an access token.
        """
        body = {
            "client_id": self.rcm.RAINDROP_CLIENT_ID,
            "client_secret": self.rcm.RAINDROP_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": self.rcm.RAINDROP_REFRESH_TOKEN,
        }
        return body


class RaindropNewAccessTokenGetter:
    """Process for new user to get a valid Oauth2 access token.

    #TODO: Wrote ages ago. Restructured when creating multiple RaindropOauth and
    EnvManager classes. Functionality untested.

    #TODO: Will need to be passed a RaindropCredentialsManager

    NOTE: Will open a web browser requiring user to manually click to
    confirm authentication + paste the resulting url back into the console.
    """

    def __init__(
        self, rcm: RaindropCredentialsManager, evfm: EnvironmentVariablesFileManager
    ) -> None:
        """
        Initialize a an Get New Oauth object with the required client id and client
        secret from a .env file.
        """
        self.rcm = rcm
        self.evfm = evfm

    def new_token_process_runner(self) -> Optional[int]:
        """DO NOT USE - has errors.
        Main "driver" method that orchestrates the entire oauth process and is
        responsible for calling all other methods in the class.

        Raises an error if an oauth token exists in .env.

        Otherwise, runs the full oauth process.

        Returns the new auth code.
        """
        # try:
        #     if os.getenv("RAINDROP_OAUTH_TOKEN"):
        #         raise ExistingTokenError(self.TOKEN_EXISTS_ERROR)
        #     else:
        #         self._open_authorization_code_url()
        #         auth_code_url = self._user_paste_valid_auth_code_url()
        #         auth_code = self._parse_authorization_code_url(auth_code_url)
        #         headers = self.HEADERS
        #         body = self._new_token_create_body(auth_code)
        #         response = self._make_request(body)
        #         self._response_validator(response)
        #         oauth_token = self._extract_oauth_token(response)
        #         # TODO : Add writing the refersh token to .env
        #         self._write_new_body_to_env(oauth_token)
        #         return f"Success! Oauth {oauth_token} written to .env."
        # except UserCancelledError:
        #         # TODO : Figure out how this works
        #         logger.warning("OAuth process cancelled by the user.")
        #         return "Oauth failed."
        unfinished_warning.warn(
            "You wrote this before you understood what was happening - needs revising"
        )
        raise (BadProgrammerError)

    def _open_authorization_code_url(self) -> bool:
        """
        First step of oauth is to allow the "application" access.  (This is the
        application you create within Raindrop).  Requires our app to have a web url -
        we use local host (as defined on init).

        Local host  will get a load error (obviously) but that is fine - the code
        raindrop passes to the url will still work.

        Returns
        -------
        bool
            Always returns True after opening the web page.
        """
        logger.info(
            "NEXT: A browser window will take you to raindrop.io. "
            'You need to click "Agree". You will then be redirected to an new URL that '
            "contains the code. Copy this url and paste into the terminal where prompted."
        )
        ac_client_url = f"?client_id={self.rcm.RAINDROP_CLIENT_ID}"
        ac_redirect_url = f"&redirect_uri={self.rcm.REDIRECT_URI}"
        full_ac_url = self.rcm.AUTH_CODE_BASE_URL + ac_client_url + ac_redirect_url
        webbrowser.open(full_ac_url)

    def _user_paste_valid_auth_code_url(self) -> str:
        """
        Request the user input paste the url from the authorization code redirect.

        Validates the output using regex & on invalid input, request the user try
        again.

        Regex requires string start "http://localhost/?code=" and then is followed
        by a code made up of any combination of lower case letters, numbers and -.
        The string must then end.

        If the user passes "q" it raises a UserCancelledError which terminates the
        programme.
        """
        pattern = r"^http://localhost/\?code=[a-z0-9\-]+$"
        code_url = ""
        while True:
            code_url = input("\nPaste the full returned url (with https etc) here: ")
            if re.match(pattern, code_url):
                break
            elif code_url == "q":
                raise UserCancelledError("User cancelled the OAuth process.")
            else:
                logger.warning(
                    "Invalid URL. The full format to paste should look like: "
                    "http://localhost/?code=aa1a1aa1-1a11-1111-a111-aa1111111aa1"
                    "\nPlease make sure it is in the correct format and re-try."
                    "\nOr PRESS 'Q' to quit the oauth process (if raindrop.io failed to "
                    "open correctly or the link format give is incorrect.)"
                )
        return code_url

    def _parse_authorization_code_url(self, auth_code_url: str) -> str:
        """
        Strips out the authorization code Raindrop returns in a URL.

        Parameters
        ----------
        auth_code_rul: str
            A authorizataion_code_url including an auth code, in a validated format.
        """
        url = urlparse(auth_code_url)
        query_dict = parse_qs(url.query)
        authorization_code = query_dict.get("code")[0]
        return authorization_code

    def _new_token_create_body(self, authorization_code: str) -> dict[str, str]:
        """
        Create body/data dict required for a new Oauth request.
        """
        body = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": self.rcm.RAINDROP_CLIENT_ID,
            "client_secret": self.rcm.RAINDROP_CLIENT_SECRET,
            "redirect_uri": "http://localhost",
        }
        return body
