from datetime import datetime, timezone
import json
import os
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs
import webbrowser

from dotenv import load_dotenv
import ipdb
from loguru import logger
import requests
from requests import Request, Response
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential 

load_dotenv()

class Raindrop:
    """
    Class for instantiating a Raindrop object from an individual Raindrop JSON.

    Instance variables are those required for:

        a) saving to "tracked_favourites"
        b) writing to Todoist

    Attributes
    ----------
    id : str
        The unique identifier of the Raindrop.
    created_time : datetime
        The time when the Raindrop was created.
    parsed_time : datetime
        The time when the Raindrop was parsed by the script.
    title : str
        The title of the Raindrop.
    notes : str
        Any notes attached to the Raindrop.
    link : str
        The hyperlink associated with the Raindrop.

    """

    def __init__(self, raindrop_json: Dict) -> None:
        """
        Instantiate a Raindrop object from an API output JSON for a single Raindrop.

        Parameters
        ----------
        raindrop_json : dict
            The JSON object output by the Raindrop API, representing a single Raindrop.
        """

        self.id = raindrop_json["_id"]
        self.created_time = raindrop_json["created"]
        self.parsed_time = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        self.title = raindrop_json["title"]
        self.notes = raindrop_json["note"]
        self.link = raindrop_json["link"]

    def to_dict(self) -> None:
        """
        Convert the Raindrop object to a dictionary (for saving to the JSON database).

        Returns
        -------
        dict
            A dictionary representation of the Raindrop object.
        """

        return {
            "id": self.id,
            "created_time": self.created_time,
            "parsed_time": self.parsed_time,
            "title": self.title,
            "notes": self.notes,
            "link": self.link,
        }


class RaindropsProcessor:
    """
    A class to process the API response from the Raindrops "by category" endpoint.

    Attributes
    ----------
    all_raindrops_api_response : dict
        The API response containing all Raindrops.
    """

    def __init__(self, all_raindrops_api_response: Dict[str, Any]):
        """
        Parameters
        ----------
        all_raindrops_api_response : dict
            The API response containing all Raindrops.
        """
        self.all_raindrops_api_reponse = all_raindrops_api_response

    def process_favourites(self) -> List[Raindrop]:
        """
        Process a Raindrop API response, extract the favourites, remove previously
        processed favourites, and convert the new favourites into Raindrop objects.

        Returns
        -------
        List[Raindrop]
            List of newly favourited Raindrop objects ready to be sent to Todoist.
        """

        all_favourited_raindrops: List[Dict] = self._extract_all_favourited_raindrops()
        logger.info(f"Includes {len(all_favourited_raindrops)} favourites")
        logger.debug(f"Favourites: {all_favourited_raindrops}")

        newly_favourited_raindrops = self._remove_raindrops_previously_favourited(
            all_favourited_raindrops
        )

        raindrop_objects_for_todoist = self._convert_favourites_to_raindrop_objects(
            newly_favourited_raindrops
        )
        logger.info(
            f"{len(raindrop_objects_for_todoist)} Raindrop objects created for todoist"
        )

        self._update_previously_favourited(raindrop_objects_for_todoist)

        return raindrop_objects_for_todoist

    def _update_previously_favourited(
        self, raindrop_objects_for_todoist: List[Raindrop]
    ) -> bool:
        """
        Update the list of previously favorited Raindrop objects.

        Parameters
        ----------
        raindrop_objects_for_todoist : List[Raindrop]
            List of Raindrop objects that have been favorited and are set to be sent to
            Todoist.

        Returns
        -------
        bool
            Returns True after updating the list of previously favorited Raindrop
            objects.
        """

        db_manager = DatabaseManager()
        db_manager.update_database(raindrop_objects_for_todoist)

        return True

    def _convert_favourites_to_raindrop_objects(
        self, newly_favourited_raindrops: List[Dict]
    ):
        """
        Convert a list of newly favorited Raindrop JSONs to Raindrop objects ready for
        passing to Todoist.

        Parameters
        ----------
        newly_favourited_raindrops : List[Dict]
            List of Raindrop JSONs that are newly favorited.

        Returns
        -------
        List[Raindrop]
            List of Raindrop objects converted from the newly favorited Raindrop JSONs.
        """

        raindrop_objects_for_todoist = []

        for raindrop_json in newly_favourited_raindrops:
            raindrop_objects_for_todoist.append(Raindrop(raindrop_json))

        return raindrop_objects_for_todoist

    def _remove_raindrops_previously_favourited(
        self, all_favourited_raindrops: List[Dict]
    ):
        """
        Takes a list of favourited Raindrop objects and compares them to the list of
        previously processed favourites.

        Returns a list of newly favourited Raindrop objects, if any.

        Parameters
        ----------
        all_favourited_raindrops : List[Dict]
            List of all Raindrop JSONs that are favorited.

        Returns
        -------
        List[Dict]
            List of Raindrop JSONs that are newly favorited.
        """

        db_manager = DatabaseManager()

        latest_db = db_manager.get_latest_database()
        already_processed_raindrops = latest_db["Processed Raindrops"]
        logger.info(f"{len(already_processed_raindrops)} previously favourited")

        if already_processed_raindrops:
            already_processed_ids = {rd["id"] for rd in already_processed_raindrops}

            new_favourited_raindrops = [
                raindrop
                for raindrop in all_favourited_raindrops
                if raindrop["_id"] not in already_processed_ids
            ]

        else:
            new_favourited_raindrops = all_favourited_raindrops

        logger.info(f"Newly favourited raindrops: {new_favourited_raindrops}")
        return new_favourited_raindrops

    def _extract_all_favourited_raindrops(self) -> List[Dict]:
        """
        Finds all favourited Raindrops in an Raindrop API response. Designed to work
        with collection_id endpoint, but likely to work with others.

        Favourite status is indicated by "important": True.

        BEWARE:  It seems to be possible for a Raindrops not to have an "important" key.

        Returns
        -------
        List[Dict]
            List of all Raindrop JSONs that are favorited.
        """

        all_favourited_raindrops = []

        for raindrop in self.all_raindrops_api_reponse:
            if raindrop.get("important") == True:
                all_favourited_raindrops.append(raindrop)

        return all_favourited_raindrops


class DatabaseManager:
    """
    A class to manage JSON files which serve as the database for the project.

    The database stores basic information about every favourited raindrop that has been
    processed and successfully created as a task in Todoist.

    The database is stored in 'database' in the project root.

    A metafile, stored in 'metafile' in the project root, tracks the path to the most
    recent database version.

    Attributes
    ----------
    database_directory : str
        Directory where the database files are located.
    metafile_directory : str
        Directory where the metafile is located.
    metafile_path : str
        Path of the metafile.
    """

    def __init__(self):
        self.database_directory = (
            "/Users/chrisbillows/Documents/CODE/MY_GITHUB_REPOS/"
            "raindrop-todoist-syncer/database"
        )
        self.metafile_directory = (
            "/Users/chrisbillows/Documents/CODE/MY_GITHUB_REPOS/"
            "raindrop-todoist-syncer/metafile"
        )
        self.metafile_path = (
            "/Users/chrisbillows/Documents/CODE/MY_GITHUB_REPOS/"
            "raindrop-todoist-syncer/metafile/metafile.txt"
        )

    def update_database(self, new_favourited_raindrop_objects: List[Raindrop]) -> bool:
        """
        Update the database with new favourite raindrop objects and update the metafile.

        Parameters
        ----------
        new_favourited_raindrop_objects : List[Raindrop]
            List of Raindrop objects that are newly favourited.

        Returns
        -------
        bool
            True if database and metafile are updated successfully.
        """

        rds_to_add = []
        for raindrop_object in new_favourited_raindrop_objects:
            rds_to_add.append(raindrop_object.to_dict())

        db: Dict[str, List[Dict[str, Any]]] = self.get_latest_database()

        previous_rds: List = db["Processed Raindrops"]
        logger.info(f"Previous db length {len(previous_rds)}")

        db["Processed Raindrops"] = previous_rds + rds_to_add
        logger.info(f"New db length {len(db['Processed Raindrops'])}")

        file_number = len(os.listdir(self.database_directory)) + 1

        output_file = (
            f"{file_number:03d}_processed_raindrops_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )

        new_database_file_name = os.path.join(self.database_directory, output_file)

        with open(new_database_file_name, "w") as f:
            json.dump(db, f, indent=4)
        logger.info(f"New db file created: {new_database_file_name}")

        with open(self.metafile_path, "w") as metafile:
            metafile.write(new_database_file_name)
        logger.info(f"Metafile updated")

        return True

    def get_latest_database(self) -> Dict[str, Any]:
        """
        Load the most recent JSON database into memory or, if none exists,
        create a new, empty, database (with "Processed Raindrops" as the key, and an
        empty list as the value).

        Returns
        -------
        Dict[str, Any]
            The latest JSON database.
        """

        os.makedirs(self.metafile_directory, exist_ok=True)
        os.makedirs(self.database_directory, exist_ok=True)

        if len(os.listdir(self.metafile_directory)) == 0:
            self._create_new_database_and_metafile()

        with open(self.metafile_path, "r") as metafile:
            latest_version = metafile.read().strip()

        with open(latest_version, "r") as f:
            json_data = f.read()
            latest_db = json.loads(json_data)

        return latest_db

    def _create_new_database_and_metafile(self) -> bool:
        """
        Create a new, empty JSON database and metafile, essentially from template.

        Returns
        -------
        bool
            True if a new JSON database and metafile are created successfully.
        """
        processed_raindrops_blank = {"Processed Raindrops": []}

        output_file = (
            "001_processed_raindrops_" f"{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )

        database_file_name = os.path.join(self.database_directory, output_file)

        with open(database_file_name, "w") as f:
            json.dump(processed_raindrops_blank, f, indent=4)

        with open(self.metafile_path, "w") as metafile:
            metafile.write(database_file_name)

        return True


class RaindropClient:
    """
    Handles interactions with the Raindrop.io API.

    DO NOT USE - currently in development (refactor RaindropClient).

    The API returns paginated responses of (default) 25 raindrops(rds). This could be
    increased to 50 (source: https://developer.raindrop.io/v1/raindrops/multiple) but
    was unreliable in limited testing.

    attributes:
        BASE_URL (str)           : API uri
        RAINDROPS_PER_PAGE (int) : total rds per paginated page
        MAX_ALLOWED_PAGES (int)  : arbitrary fallback to prevent infinte loops etc. 200
                                   pages @ 25 rds per page = 5,000 rds

    example:
    >>> raindrop_client = RaindropClient()
    >>> all_raindrops = raindrop_client.get_all_raindrops()
    """
    BASE_URL = "https://api.raindrop.io/rest/v1"
    RAINDROPS_PER_PAGE = 25
    MAX_ALLOWED_PAGES = 200

    def __init__(self) -> None:
        """
        Initializes an instance of Raindrop Client.

        instance vars:
            raindrop_oauth_token (str) : Oauth token extracted from .env
            headers (dict)             : HTTP request header
        """
        self.raindrop_oauth_token = os.getenv("RAINDROP_OAUTH_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.raindrop_oauth_token}"}
        logger.info("Raindrop Client initalised")

    def get_all_raindrops(self) -> List[Dict[str, Any]]:
        """
        Gets all rds from the API "{collection_id}" endpoint.

        The primary class method.  It structures and makes API requests. It extracts
        validation data. It validates the responses, the rds themselves, and the final
        concatenated response payload. If data inconsistency is suggested, the
        process raises an error and halts.

        Structured to allow further validation checks etc. to be easily added.

        Rds are served in pages (default 25).
        Endpoint info: https://developer.raindrop.io/v1/raindrops/multiple.

        NOTE: collection_id is defaulted to 0 which requests all collections. Individual
        collections can be called if required in the future.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary
            represents a single raindrop. Returns an empty list if no raindrops are
            found.

        Raises:
            ValueError: On various conditions. TODO: Complete list.
        """
        logger.info("Get all raindrops called")
        cumulative_rds = []
        page = 0
        while True:
            response = self._make_api_call(page)
            self._response_validator(response)
            data = response.json()
            if page == 0:
                benchmark_count = self._extract_benchmark_count(data)
                target_pages = self._calculate_max_pages(benchmark_count)
            self._data_validator(data, benchmark_count)
            current_rds = data.get("items", []) 
            self._individual_rd_validator(current_rds)
            cumulative_rds.extend(current_rds)
            page += 1
            if page >= target_pages:
                break
        self._cumulative_rds_validator(cumulative_rds, current_rds, benchmark_count)
        return cumulative_rds

    def _core_api_call(self, page: int) -> Response:
        collection_id = 0
        params = {"perpage": self.RAINDROPS_PER_PAGE, "page": page}
        response = requests.get(
            f"{self.BASE_URL}/raindrops/{collection_id}/",
            headers=self.headers,
            params=params,
        )
        response.raise_for_status()
        return response


    @retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, max=10), 
    retry=retry_if_exception_type(requests.exceptions.RequestException)
    )
    def _make_api_call(self, page: int) -> Response:
        return self._core_api_call(page)


    def _response_validator(self, response: Response) -> None:
        """
        --DEPRECARED--  Replaced with raise_for_status() in _make_api_call. Kept to 
        faciliate any additional response validation required in future.
        """
        pass

    def _extract_benchmark_count(self, data: Dict[str, Any]) -> int:
        """
        Creates a variable benchmark_rd_count for the total rds on the server.

        Every Raindrop.io collections endpoint response has a field 'count'. This method
        extracts this value into the variable benchmark_rd_count

        Extracts response_json['count'] from the first

        parameters:
            response [response] : the full API requests.response object
        """
        count = data.get("count")
        if count is None:
            if "count" in data:
                raise ValueError("The 'count' key was found in the response data, but its value was None.")
            else:
                raise ValueError("The 'count' key was not found in the response data.")
        return count

    def _calculate_max_pages(self, benchmark_rd_count: int) -> int:
        """
        Placeholder: Calculates how many api calls are required to get all results (i.e.
        the total number of pages to be extracted at RAINDROPS_PER_PAGE)
        """
        max_pages, remainder = divmod(benchmark_rd_count, self.RAINDROPS_PER_PAGE)
        if remainder:
            max_pages += 1
        if max_pages > self.MAX_ALLOWED_PAGES:
            raise ValueError("Max pages greater than allowed. Adjust setting in class constant to override.")
        return max_pages

    def _data_validator(self, data: Dict[str, Any], benchmark_count: int) -> None:
        if data.get("result") is not True:
            raise ValueError("API Result False")

        new_count = data.get("count")
        if new_count != benchmark_count:
            raise ValueError(
                f"Count changed during process. Benchmark count: {benchmark_count}. New count: {new_count}."
            )

    # def _individual_rd_validator(self, rds: List[Dict[str, Any]]) -> None:
    #     """
    #     Validate each individual rd. Basically, if ANY rd doesn't have an rd this will
    #     raise and abort the process. Overkill?
    #     """
    #     if any(rd.get("_id") is None for rd in rds):
    #         raise ValueError("Invalid raindrop item found in current collection.")

    def _individual_rd_validator(self, rds: List[Dict[str, Any]]) -> None:
        """
        Validate each individual rd. If any rd doesn't have an _id of type int, 
        this will raise a ValueError. If the _id length is not 9 digits, 
        it will log a warning but continue processing.
        """
        if any(not isinstance(rd.get("_id"), int) for rd in rds):
            raise ValueError("Invalid raindrop item found in current collection: _id is not of type int.")
        # TODO:     Finish, logger line added at top but needs to a child logger
        
        # TODO      There are also additional tests written in tests/unit/test_rd_client.py
        # TODO      They test for 
        # TODO              a) the 9 digits (so we need that to test if logged)
        # TODO              b) if a rd _id is blank
        
        # TODO      Do we want to fail on these, log these or ignore these?
        
        for rd in rds:
            if len(str(rd.get("_id"))) != 9:
                logger.warning(f"Raindrop with _id {rd.get('_id')} does not have 9 digits.")

    def _cumulative_rds_validator(
        self,
        cumulative_rds: List[Dict[str, Any]],
        current_rds: List[Dict[str, Any]],
        benchmark_count: int,
    ) -> None:
        """
        Checks the expected total rds were collected, and in the correct order.
        
        The rds are collected together, 25 by 25 (or RAINDROPS_PER_PAGE), like animals
        boarding Noah's Ark. 
        
        Current checks:
            - the total number of collected rds matches the expected. (The 'count' which
              is extracted from the first API call and checked on each subdequent API
              call).
            - checks the rds were collected in the correct order, e.g. by page, 25, 25,
              3, and not 25, 3, 25.
                
        Returns:
            None:  returns None if data is valid 
        
        Raises:
            ValueError:
                - If the total number of collected raindrops doesn't match the expected 
                  benchmark count.
                - If the number of raindrops on the last page does not match the 
                  expected length of the last page.
        """
        if len(cumulative_rds) != benchmark_count:
            raise ValueError("Total raindrops extracted not expected length.")

        expected_len_last_page = benchmark_count % self.RAINDROPS_PER_PAGE
        if len(current_rds) != expected_len_last_page:
            raise ValueError(
                f"Last page results not expected length. Expected: {expected_len_last_page}, Got: {len(current_rds)}"
            )


class ExistingTokenError(Exception):
    pass

class MissingRefreshTokenError(Exception):
    pass

class UserCancelledError(Exception):
    pass


class RaindropOauthHandler:
    """
    Class with one none private method to generate a new oauth token and write it the
    .env file.

    REQUIRED: manually delete any existing (expired) oauth token in .env

    Run from raindrop_oauth_gen.py.

    NOTE: Will open a web browser requiring user to manually click to
    confirm authentication + paste the resulting url back into the console.

    Constants
    ---------
    AUTH_CODE_BASE_URL :



    Attributes
    ----------
    REDIRECT_URI : str
        The redirect URI for the OAuth process.
    RAINDROP_CLIENT_ID : str
        The client ID for the Raindrop API, fetched from environment variables.
    RAINDROP_CLIENT_SECRET : str
        The client secret for the Raindrop API, fetched from environment variables.
    """

    TOKEN_EXISTS_ERROR = (
        "An OAuth token already exists in .env. "
        "Please manually delete it and try again.\n"
        "(Manual deletion helps ensure tokens aren't erased "
        "in error.)"
    )
    AUTH_CODE_BASE_URL = "https://raindrop.io/oauth/authorize"
    REDIRECT_URI = "http://localhost"
    HEADERS = {"Content-Type": "application/json"}

    def __init__(self) -> None:
        """
        Initialize a an Get New Oauth object with the required client id and client
        secret from a .env file.
        """
        self.env_file = ".env"
        self.RAINDROP_CLIENT_ID = os.getenv("RAINDROP_CLIENT_ID")
        self.RAINDROP_CLIENT_SECRET = os.getenv("RAINDROP_CLIENT_SECRET")
        self.RAINDROP_REFRESH_TOKEN = os.getenv("RAINDROP_REFRESH_TOKEN")
            
    def new_token_process_runner(self) -> Optional[int]:
        """
        Main "driver" method that orchestrates the entire oauth process and is
        responsible for calling all other methods in the class.

        Raises an error if an oauth token exists in .env.

        Otherwise, runs the full oauth process.

        Returns the new auth code.
        """
        try:
            if os.getenv("RAINDROP_OAUTH_TOKEN"):
                raise ExistingTokenError(self.TOKEN_EXISTS_ERROR)
            else:
                self._open_authorization_code_url()
                auth_code_url = self._user_paste_valid_auth_code_url()
                auth_code = self._parse_authorization_code_url(auth_code_url)
                headers = self.HEADERS
                body = self._new_token_create_body(auth_code)
                response = self._make_request(body)
                self._response_validator(response)
                oauth_token = self._extract_oauth_token(response)
                # TODO : Add writing the refersh token to .env
                self._write_token_to_env(oauth_token)
                return f"Success! Oauth {oauth_token} written to .env."
        except UserCancelledError:
                # TODO : Figure out how this works
                logger.warning("OAuth process cancelled by the user.")
                return "Oauth failed."
            
    def refresh_token_process_runner(self) -> Optional[int]:
        """
        """
        if not os.getenv("RAINDROP_REFRESH_TOKEN"):
            raise MissingRefreshTokenError("No refresh token in .env. Refresh aborted")
        else:
            headers = self.HEADERS
            body = self._refresh_token_create_body()
            response = self._make_request(body)
            self._response_validator(response)
            oauth_token = self._extract_oauth_token(response)
            self._write_token_to_env(oauth_token)
            # TODO: Add check to see if refresh token has changed and
            # write to .env if so.
            return f"Success! Oauth {oauth_token} written to .env."

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
        ac_client_url = f"?client_id={self.RAINDROP_CLIENT_ID}"
        ac_redirect_url = f"&redirect_uri={self.REDIRECT_URI}"
        full_ac_url = self.AUTH_CODE_BASE_URL + ac_client_url + ac_redirect_url
        webbrowser.open(full_ac_url)
        return True

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

    def _new_token_create_body(self, authorization_code: str) -> Dict[str, str]:
        """
        Create body/data dict required for a new Oauth request.
        """
        body = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": self.RAINDROP_CLIENT_ID,
            "client_secret": self.RAINDROP_CLIENT_SECRET,
            "redirect_uri": "http://localhost",
        }
        return body
    
    def _refresh_token_create_body(self) -> Dict[str, str]:
        """
        Create body/data dict required to refresh an Oauth token.
        """
        body = {
            "client_id": self.RAINDROP_CLIENT_ID,
            "client_secret": self.RAINDROP_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": self.RAINDROP_REFRESH_TOKEN
        }
        return body
 
    def _make_request(self, body) -> Request:
        """
        Makes the oauth request and returns a Request object.
        """
        headers = self.HEADERS
        data = body
        oauth_response = requests.post(
            "https://raindrop.io/oauth/access_token",
            headers=headers,
            data=json.dumps(data),
        )
        return oauth_response

    def _response_validator(self, response):
        if response.status_code != 200:
            raise ValueError(f"Response status code is not 200 (as required in the docs). Status code was {response.status_code} - {response.text}")
    
        if response.json().get("access_token") is None:
            raise ValueError(f"Response code 200 but no token in response. Full response {response.json()}")
        
    def _extract_oauth_token(self, oauth_response):
        data = oauth_response.json()
        access_token = data.get("access_token")
        logger.info(f"Your access token is {access_token}")
        return access_token

    def _write_token_to_env(self, oauth_token):
        """
        Write the new oauth token to the .env file.

        Could be unstable if I have concurrent instances (unlikely but beware).
        """
        env_file = ".env"
        token_key = "RAINDROP_OAUTH_TOKEN"
        # TODO - this doesn't work unless the oauth is last?
        with open(self.env_file, "a+") as f:
            f.seek(0, 2)
            if f.tell() > 0:
                f.seek(f.tell() - 1)
            if f.read(1) != "\n":
                f.write("\n")
            f.write(f"{token_key}='{oauth_token}'\n")
        return True
