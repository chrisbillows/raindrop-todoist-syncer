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
        # TODO: Add error handling. Raindrop class will crash in event of a missing 
        # TODO  field. (rd_processor has a skipped failing test in the event of a
        # TODO  raindrop missing a field).
        
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
    A class to process a list of all a user's Raindrops,

    Class Attributes:
    all_raindrops_api_response :  The list of raindrops (rds) collected from multiple API
                                  calls by RaindropClient.
    """
    def __init__(self, all_rds: Dict[str, Any]):
        """
        Initalise an instance of the Raindrops Process, taking all_rds as state.
        
        Parameters:
            all_rds : list of all a users raindrops(rds).
            
        """
        self.all_rds = all_rds

    def newly_favourited_raindrops_extractor(self) -> List[Raindrop]:
        """
        Process favourited rds from a list of rds.
        
        This is the primary method for extracting newly favourited (unprocessed) rds 
        from a list of rds. 
        
        It takes a list of rds and extracts favourited rds. Compares this with the 
        favourites the system has already processed, producing a list of newly  
        favourited/unprocessed rds. Converts these to Raindrops objects for passing to 
        Todoist.
        
        TODO: Currently updates the database.  This should not happen until AFTER tasks
        creation is a success. That is when an fav rd is "processed".
        
        Returns:
        -------
        raindrop_objects_for_todoist:  List of newly favourited rds as Raindrop objects 
                                       ready to be sent to Todoist.
        """
        all_favs = self._extract_all_fav_rds()
        tracked_favs = self._fetch_tracked_favs()
        untracked_favs = self._extract_untracked_favs(all_favs, tracked_favs)
        rd_objects = self._convert_to_rd_objects(untracked_favs)
        # TODO: This function updates the db - BEFORE the todoist tasks are successfully created.
        # TODO: Keep for now, or the code will not function!! 
        self._update_previously_favourited(rd_objects)
        return rd_objects
    
    def _extract_all_fav_rds(self) -> List[Dict]:
        """
        Finds all favourited Raindrops in an Raindrop API response. Designed to work
        with collection_id endpoint, but likely to work with others.

        Favourite status is indicated by {"important": True}.

        BEWARE:  It seems rds do not to have an "important" key UNLESS favourited.

        Returns
        -------
        List[Dict]
            List of all Raindrop JSONs that are favorited.
        """
        fav_rds = []
        for raindrop in self.all_rds:
            if raindrop.get("important") == True:
                fav_rds.append(raindrop)
        logger.info(f"Includes {len(fav_rds)} favourites.")
        # logger.debug (f"Favourites: {fav_rds}")
        return fav_rds
    
    def _fetch_tracked_favs(self):
        db_manager = DatabaseManager()
        tracked_favs = db_manager.get_latest_database()["Processed Raindrops"]
        logger.info(f"A total of {len(tracked_favs)} favourited rds previously tracked")
        return tracked_favs
    
    def _extract_untracked_favs(self, all_favs: List[Dict], tracked_favs: List[Dict]):
        """
        Takes a list of favourited Raindrop objects and compares them to the list of
        previously processed favourites.

        Returns a list of newly favourited Raindrop objects, if any.

        Parameters:
            fav_rds         : List of all Raindrop JSONs that are favorited.

        Returns:
            unprocessed_rds : List of Raindrop JSONs that are newly favorited.
        """
        tracked_fav_ids = {rd["id"] for rd in tracked_favs}
        untracked_favs = [rd for rd in all_favs if rd["_id"] not in tracked_fav_ids]
        logger.info(f"Untracked favourites found: {untracked_favs}")
        return untracked_favs
    
    def _convert_to_rd_objects(self, untracked_favs: List[Dict]) -> List[Raindrop]:
        """
        Convert a list of newly favorited Raindrop JSONs to Raindrop objects ready for
        passing to Todoist.

        Parameters:
            unprocessed_rds : List of Raindrop JSONs that are newly favorited.

        Returns:
            rd_objects      : List of rd objects converted from the unprocessed rds.
        """
        rd_objects = []
        for raindrop_json in untracked_favs:
            rd_objects.append(Raindrop(raindrop_json))
        logger.info(f"{len(rd_objects)} Raindrop object(s) created.")
        return rd_objects

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
        # TODO - this is the functionality that needs to be moved latter in the process
        # flow.
        db_manager = DatabaseManager()
        db_manager.update_database(raindrop_objects_for_todoist)
        logger.info(f"Updated database with {len(raindrop_objects_for_todoist)} new favs.")
        return True


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
        self.database_directory = "database"
        self.metafile_directory = "metafile"
        self.metafile_path = "metafile/metafile.txt"

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
    A class to handle interactions with the Raindrop.io API.

    The API returns paginated responses of 25 raindrops(rds). 25 is the default. It can
    be increased to 50 (source: https://developer.raindrop.io/v1/raindrops/multiple) but
    was unreliable in limited testing.

    Attributes:
        BASE_URL (str)           : API uri
        RAINDROPS_PER_PAGE (int) : total rds per paginated page
        MAX_ALLOWED_PAGES (int)  : arbitrary fallback to prevent infinte loops etc. 200
                                   pages @ 25 rds per page = 5,000 rds

    Example:
    >>> raindrop_client = RaindropClient()
    >>> all_raindrops = raindrop_client.get_all_raindrops()
    """
    BASE_URL = "https://api.raindrop.io/rest/v1"
    RAINDROPS_PER_PAGE = 25
    MAX_ALLOWED_PAGES = 200

    def __init__(self) -> None:
        """
        Initializes an instance of Raindrop Client.

        Instance variables:
            raindrop_oauth_token (str) : Oauth token extracted from .env
            headers (dict)             : HTTP request header
        """
        self.raindrop_oauth_token = os.getenv("RAINDROP_OAUTH_TOKEN")
        self.headers = {"Authorization": f"Bearer {self.raindrop_oauth_token}"}
        logger.info("Raindrop Client initalised")

    def get_all_raindrops(self) -> List[Dict[str, Any]]:
        """
        Retrieve all raindrops from the Raindrop.io API.

        This is the primary method for fetching and validating raindrops from the API. 
        It paginates through the API responses and performs several validation checks 
        to ensure the data is consistent.
        
        Note: 
            The `collection_id` defaults to 0, fetching all collections. You can specify 
            other collection IDs if needed.   

        Returns:
            List        : A list of dictionaries where each dictionary represents a 
                          single raindrop. Returns an empty list if no raindrops are
                          found.
        Raises:
            ValueError  : Raised at lower levels, see validator methods in particular.
            
        Also:
            API Endpoint Documentation: https://developer.raindrop.io/v1/raindrops/multiple.
            Rds are served in pages (default 25).
            Methods structured this way to allow further validation checks etc. to be 
            easily added.
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
            logger.debug(f"Length of culmative rds: {len(cumulative_rds)}")
            page += 1
            if page >= target_pages:
                logger.debug(f"Page({page}) equals target pages({target_pages})")
                break
        self._cumulative_rds_validator(cumulative_rds, current_rds, benchmark_count)
        return cumulative_rds

    def _core_api_call(self, page: int) -> Response:
        """
        Makes the API call.
        
        Parameters:
            page     : A page to request from the full paginated list. 
        
        Returns:
            response : The API response
        """
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
        """
        A retry logic wrapper for the core API caller.
        
        The retry logic makes three calls with increasing waits. If the headers contain 
        rate limit status - this is logged. NOTE: 200 responses should contain headers, 
        but this is not currently enforced. 
               
        Parameters:
            page     : A page to request from the full paginated list. 
        
        Returns:
            response : The API response
        """
        response = self._core_api_call(page)
        if 'x-ratelimit-remaining' in response.headers and 'x-ratelimit-limit' in response.headers:
            logger.debug(f"API calls remaining before reset: {response.headers['x-ratelimit-remaining']}/{response.headers['x-ratelimit-limit']}")
        else:
            logger.warning(f"API headers does not include rate limit status.")        
        return response

    def _response_validator(self, response: Response) -> None:
        """
        --DEPRECATED-- Validation for the response status.
        
        Now replaced with raise_for_status() in _make_api_call. Kept to faciliate any 
        additional response validation required in future.
        """
        pass

    def _extract_benchmark_count(self, data: Dict[str, Any]) -> int:
        """
        Extract and store the "benchmark" total of the user's rds on the server.

        This method captures the benchmark from the first API call. This total could        
        could change if the user adds or removes rds during the collection process. Or 
        with an error.
        
        Parameters:
            data       : The JSON output from the response i.e. response.json() 
            
        Raises:
            ValueError : If no 'count' field is found, if the value of 'count' is None
                         or the value is negative.
        """
        count = data.get("count")
        logger.debug(f"Benchmark count value: {count}")
        if count is None:
            if "count" in data:
                raise ValueError("The 'count' key was found in the response data, but its value was None.")
            else:
                raise ValueError("The 'count' key was not found in the response data.")
        if count < 0:
            raise ValueError("The 'count' key was found in the response data, but it's value was negative.")
        return count

    def _calculate_max_pages(self, benchmark_rd_count: int) -> int:
        """
        Calculates how many api calls are required to collect all rds.
        
        This takes the benchmark_rd_count (the total rds expected) and divides it by
        the constant RAINDROPS_PER_PAGE. This is passed back to `get_all_raindrops` as 
        `target_pages` which sets the number of calls to make to the API.
        
        NOTE: This should not allow for any infinite loops. Divmod works correctly for 
        0, 1, etc. Negative benchmark counts raise an error. MAX_ALLOWED_PAGES caps 
        calls even if raindrop.io were to pass a huge benchmark count.
        
        Parameters:
            benchmark_rd_count  : the users total rds on the raindrop.io server
            
        Returns:
            max_pages:          : the total number of pages required to call
        """
        max_pages, remainder = divmod(benchmark_rd_count, self.RAINDROPS_PER_PAGE)
        logger.debug(f"Max pages, remainder: {max_pages, remainder}")
        if remainder:
            max_pages += 1
        if max_pages > self.MAX_ALLOWED_PAGES:
            raise ValueError("Max pages greater than allowed. Adjust setting in class constant to override.")
        return max_pages

    def _data_validator(self, data: Dict[str, Any], benchmark_count: int) -> None:
        """
        Validate the json output from a Raindrop api response.
        
        Takes the full JSON and checks:
            - the 'count' in the current response matches the 'benchmark_count' (the
              'count' in the first API response in the current operation).
                
        Parameters:
            data       : The JSON output from the response i.e. response.json()
           
        Raises:
            ValueError : If the current 'count' doesn't match the 'benchmark' count.
        """
        if data.get("result") is not True:
            raise ValueError("API Result False")

        new_count = data.get("count")
        logger.debug(f"Count in current response: {new_count} (vs. {benchmark_count})")
        if new_count != benchmark_count:
            raise ValueError(
                f"Count changed during process. Benchmark count: {benchmark_count}. New count: {new_count}."
            )

    def _individual_rd_validator(self, rds: List[Dict[str, Any]]) -> None:
        """
        Validate individual rds returned by the Raindrop API.
        
        Takes a list of rds (typically of per page length) and checks:
            - "_id" is not len(9) : Logs a warning 
            - "_id" is None       : Raises a ValueError
            - "_id" is not an int : Raises a ValueError
        
        TODO: Monitor. This may be overkill. The API docs don't specify these 
        TODO: requirements, but logically they should apply. 
        """
        for rd in rds:
            if len(str(rd.get("_id"))) != 9:
                logger.warning(f"Raindrop with _id {rd.get('_id')} does not have 9 chars.")
        
        if any(rd.get("_id") is None for rd in rds):
            raise ValueError(f"Invalid raindrop item found in current collection: _id is None.\nRaindrop: {rd}")    
        
        if any(not isinstance(rd.get("_id"), int) for rd in rds):
            raise ValueError(f"Invalid raindrop item found in current collection: _id is not of type int.\nRaindrop: {rd}")
                
        logger.debug(f"Current rds (validated): {len(rds)}")        
        
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
            - the total number of collected rds matches the benchmark total.
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
            # TODO: Currently this function doesn't delete the old token!
            logger.warning("***MANUALLY REMOVE OLD TOKEN!***")
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
