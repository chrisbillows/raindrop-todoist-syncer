import json
from unittest.mock import Mock

import pytest
from requests import HTTPError

from raindrop import (
    Raindrop,
    RaindropAccessTokenRefresher,
    RaindropCredentialsManager,
    EnvironmentVariablesFileManager,
)


# ---------------------------------- objects -------------------------------------------


@pytest.fixture
def environmental_variables_file_manager():
    return EnvironmentVariablesFileManager()


@pytest.fixture
def raindrop_access_token_refresher():
    evfm = EnvironmentVariablesFileManager()
    rcm = RaindropCredentialsManager()
    return RaindropAccessTokenRefresher(rcm, evfm)


# ------------------------------- mock_requests_get-------------------------------------
"""
response_one and response_two created using _dummy_collections/dummy_twenty_six in
raindrop.

Gives a total count of 26 raindrops requiring two API calls (pg 0 & pg 1)
"""


@pytest.fixture
def response_one_data():
    with open("tests/mock_data/rd_api_response_one.json", "r") as f:
        return json.load(f)


@pytest.fixture
def response_two_data():
    with open("tests/mock_data/rd_api_response_two.json", "r") as f:
        return json.load(f)


@pytest.fixture
def mock_requests_get(monkeypatch, response_one_data, response_two_data):
    """Mocks requests.get method for two successful responses"""

    def _mocked_requests_get(url, headers=None, params=None):
        mock_response = Mock()
        if params == {"perpage": 25, "page": 0}:
            mock_response.json.return_value = response_one_data
            mock_response.status_code = 200
            mock_response.headers = {
                "x-ratelimit-remaining": 119,
                "x-ratelimit-limit": 120,
            }
        elif params == {"perpage": 25, "page": 1}:
            mock_response.json.return_value = response_two_data
            mock_response.status_code = 200
            mock_response.headers = {
                "x-ratelimit-remaining": 118,
                "x-ratelimit-limit": 120,
            }
        else:
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
        return mock_response

    monkeypatch.setattr("requests.get", _mocked_requests_get)


@pytest.fixture
def mock_requests_get_no_status(monkeypatch):
    """Mocks requests.get method without a status code"""

    def _mocked_requests_get_no_status(url, headers=None, params=None):
        mock_response = Mock()
        return mock_response

    monkeypatch.setattr("requests.get", _mocked_requests_get_no_status)


# ------------------------ mock_requests_response_object--------------------------------


@pytest.fixture
def response_object_200():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "Success"
    mock_response.json.return_value = {"access_token": "I am your access token"}
    return mock_response


@pytest.fixture
def response_object_400():
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad request"
    return mock_response


@pytest.fixture
def response_object_200_but_no_token():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "Success"
    mock_response.json.return_value = {}
    return mock_response


# ------------------------------- mock_db ----------------------------------------------


@pytest.fixture
def mock_db_contents() -> dict:
    """Returns content of a valid JSON database imported as a python dictionary.

    The dictionary contains one tracked Raindrop object - the processed version of a
    raindrop extracted from a Raindrop.io response.

    The dictionary contains:

    k: "Processed Raindrops" v: [<list of one Raindrop>].

    The Raindrop contains six k, v pairs including:

    k: "title", v: "Hacker News",
    k:"id", v: "28161680"
    k: "link", v: "https://news.ycombinator.com/news"

    Returns
    -------
    A python dictionary of a valid dictionary containing one tracked raindrop.
    """
    with open("tests/mock_data/mock_db.json", "r") as f:
        return json.load(f)


# --------------------------- raindrop object ------------------------------------------


@pytest.fixture
def rd_extracted_single_raindrop_dict():
    """
    Returns a dictionary representation of a single raindrop.
    In actual usage, this structure is typically extracted from a list of
    raindrops that have been processed with json.load. For testing purposes,
    this fixture loads the content of a single raindrop saved as JSON from a file.
    """
    with open("tests/mock_data/rd_api_single_rd.json", "r") as f:
        content = json.load(f)
    return content


@pytest.fixture
def raindrop_object(rd_extracted_single_raindrop_dict):
    return Raindrop(rd_extracted_single_raindrop_dict)


# ------------------------------- .env files ------------------------------------------


@pytest.fixture
def placeholder_one_liner_env():
    mock_content = "Existing content\n"
    return mock_content


@pytest.fixture
def full_env_oauth_first():
    mock_content = [
        "RAINDROP_ACCESS_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
        "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
        "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
        "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
        "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
    ]
    return "".join(mock_content)


@pytest.fixture
def full_env_oauth_middle():
    mock_content = [
        "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
        "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
        "RAINDROP_ACCESS_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
        "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
        "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
    ]
    return "".join(mock_content)


@pytest.fixture
def full_env_oauth_last():
    mock_content = [
        "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
        "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
        "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
        "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
        "RAINDROP_ACCESS_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n",
    ]
    return "".join(mock_content)
