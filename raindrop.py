from datetime import datetime, timezone

import json
import os
import requests
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs
import webbrowser

from dotenv import load_dotenv
import ipdb

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
        print(f"Includes {len(all_favourited_raindrops)} favourites")

        newly_favourited_raindrops = self._remove_raindrops_previously_favourited(
            all_favourited_raindrops
        )

        raindrop_objects_for_todoist = self._convert_favourites_to_raindrop_objects(
            newly_favourited_raindrops
        )
        print(
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
        print(f"{len(already_processed_raindrops)} previously favourited")

        if already_processed_raindrops:
            already_processed_ids = {rd["id"] for rd in already_processed_raindrops}

            new_favourited_raindrops = [
                raindrop
                for raindrop in all_favourited_raindrops
                if raindrop["_id"] not in already_processed_ids
            ]

        else:
            new_favourited_raindrops = all_favourited_raindrops

        print(f"Newly favourited raindrops: {new_favourited_raindrops}")
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
        print(f"Previous db length {len(previous_rds)}")

        db["Processed Raindrops"] = previous_rds + rds_to_add
        print(f"New db length {len(db['Processed Raindrops'])}")

        file_number = len(os.listdir(self.database_directory)) + 1

        output_file = (
            f"{file_number:03d}_processed_raindrops_"
            f"{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        )

        new_database_file_name = os.path.join(self.database_directory, output_file)

        with open(new_database_file_name, "w") as f:
            json.dump(db, f, indent=4)
        print(f"New db file created: {new_database_file_name}")

        with open(self.metafile_path, "w") as metafile:
            metafile.write(new_database_file_name)
        print(f"Metafile updated")

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
    API_URL = "https://api.raindrop.io/rest/v1"

    def __init__(self) -> None:
        self.raindrop_oauth_token = os.getenv("RAINDROP_OAUTH_TOKEN")
        self.headers = self._make_headers()

    def get_all_raindrops(self, collection_id: int = 0) -> Optional[List[Dict]]:
        """
        Fetches all raindrops for a given collection. With the default collection_id of
        0, it fetches all of the user's raindrops.

        Note:
        The API response is paginated, limited to 25 items per page with the first page
        at index 0.

        ...

        Parameters
        ----------
        collection_id : int, optional
            The ID of the collection to fetch raindrops from.
            Default is set to 0, which fetches all user's raindrops.

        Returns
        -------
        Optional[List[Dict]]
            A list of raindrops (JSON objects) retrieved from the API.
            If API request fails, it returns None.

        Raises:
        -------
            Exception: If more than 80 cycles are required for pagination.
            (Up to 2000 raindrops)
        """

        raindrops = []
        page = 0
        count = 0
        while True:
            if count > 80:
                print("Something went wrong? 80 cycles already")
                break

            params = {"perpage": 25, "page": page}

            response = requests.get(
                f"{self.API_URL}/raindrops/{collection_id}/",
                headers=self.headers,
                params=params,
            )

            if response.status_code == 200:
                raindrops += response.json()["items"]
                target_raindrops = response.json()["count"]

                if len(raindrops) < target_raindrops:
                    page += 1
                    count += 1
                    continue
                else:
                    print(f"API returned {len(raindrops)} raindrops")
                    return raindrops

            else:
                print(
                    f"Failed to get raindrops: {response.status_code}, {response.text}"
                )
                return None

    def _make_headers(self):
        """
        Create the required Oauth headers.

        Returns
        -------
        dict
            The headers dictionary with authorization details.

        """

        headers = {"Authorization": f"Bearer {self.raindrop_oauth_token}"}
        return headers


class RaindropOauthManager:
    """
    Very basic implimentation of a class to manage Raindrop API authorisation.

    Currently has only two uses.

        1) Creates an oauth if none exists, provided the .env
        contains the raindrop client id and client secret.

        2) Can be used to create a new oauth bearer when the old one expires or breaks.
        Will overwrite the old oauth bearer in the .env with the new one.

    No error handling etc.

    NOTE: Not working yet! Copy pasted version of what I used to get going.

    ALSO NOTE: Would making this work be a massive security risk???

    Attributes
    ----------
    redirect_uri : str
        The redirect URI for the OAuth process.
    RAINDROP_CLIENT_ID : str
        The client ID for the Raindrop API, fetched from environment variables.
    RAINDROP_CLIENT_SECRET : str
        The client secret for the Raindrop API, fetched from environment variables.
    """

    def __init__(self) -> None:
        """
        Initialize a new instance of RaindropOauthManager.

        If there is no OAuth token in the environment variables, a new one is generated
        and saved. Otherwise, the existing token is used.
        """

        self.redirect_uri = "http://localhost"
        self.RAINDROP_CLIENT_ID = os.getenv("RAINDROP_CLIENT_ID")
        self.RAINDROP_CLIENT_SECRET = os.getenv("RAINDROP_CLIENT_SECRET")

        if os.getenv("RAINDROP_OAUTH_TOKEN") is None:
            self.generate_and_save_new_token_to_env()
        else:
            self.RAINDROP_OAUTH_TOKEN = os.getenv("RAINDROP_OAUTH_TOKEN")

    def generate_and_save_new_token_to_env(self) -> bool:
        """
        Generate a new OAuth token and save it to environment variables.

        Returns
        -------
        bool
            Always returns True after generating and saving the token.
        """
        self.token = self._get_oauth_token()
        self._write_token_to_env()
        return True

    def _get_oauth_token(self) -> str or bool:
        """
        Generates a new oauth token using the raindrop client id, client secret and
        an authorization code generated by the get authorization code method.

        Returns
        -------
        Union[str, bool]
            The new OAuth token, or False if the token could not be generated.
        """

        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": "authorization_code",
            "code": self._get_authorization_code(),
            "client_id": self.RAINDROP_CLIENT_ID,
            "client_secret": self.RAINDROP_CLIENT_SECRET,
            "redirect_uri": "http://localhost",
        }

        response = requests.post(
            "https://raindrop.io/oauth/access_token",
            headers=headers,
            data=json.dumps(data),
        )

        if response.status_code == 200:
            data = response.json()
            try:
                access_token = data["access_token"]
                print(f"Your access token is {access_token}")
                return access_token
            except KeyError:
                print(f"No access token in the response. Full response: {data}")
                return False
        else:
            print(
                f"Failed to get access token: {response.status_code}, {response.text}"
            )
            return False

    def _get_authorization_code(self) -> bool:
        """
        First step of oauth is to allow "the application" access.  (This is the
        application you create within Raindrop).  Requires a web uri for which we use
        local host (as defined in the class).

        Local host (obviously) will get a load error but that is fine - the code
        raindrop passes to the url will still work.

        Returns
        -------
        bool
            Always returns True after opening the web page.
        """

        authorize_url = f"https://raindrop.io/oauth/authorize?client_id={self.RAINDROP_CLIENT_ID}&redirect_uri={self.RAINDROP_CLIENT_ID}"
        webbrowser.open(authorize_url)
        code_url = input("Copy and paste the (FULL) returned url: ")
        code = self._parse_authorization_code(code_url)
        return code

    def _parse_authorization_code(self, code_url: str) -> str:
        """
        Strips out the authorization code Raindrop return in a URL.

        The authorization code should return in this format:
        localhost/?code=fa71d7d0-2648-40cf-806f-5a549bb4dbb7

        """
        # urlparse() parses a URL into six components,
        # returning a 6-item named tuple: scheme://netloc/path;parameters?query#fragment
        url = urlparse(code_url)

        # parse_qs() parses a query string given as a string argument.
        # Data are returned as a dictionary.
        # The dictionary keys are the unique query variable names and
        # the values are lists of values for each name.
        query_dict = parse_qs(url.query)

        # The authorization code should be under 'code' in the dictionary
        authorization_code = query_dict.get("code")[0]
        return authorization_code

    def _write_token_to_env(self):
        """
        Write or overwrite a new oauth token to the .env file.

        Could be unstable if I have concurrent instances (unlikely but beware).

        """
        env_file = ".env"
        token_key = "RAINDROP_OAUTH_TOKEN"

        with open(env_file, "r") as file:
            env_lines = file.readlines()

        token_line_index = None
        for i, line in enumerate(env_lines):
            if line.startswith(token_key):
                token_line_index = i
                break

        new_line = f'{token_key}="{self.token}"\n'
        if token_line_index is not None:
            env_lines[token_line_index] = new_line
        else:
            env_lines.append(new_line)

        with open(env_file, "w") as file:
            file.writelines(env_lines)

        return True
