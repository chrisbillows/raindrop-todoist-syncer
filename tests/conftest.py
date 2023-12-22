import json
from unittest.mock import Mock

import pytest
from requests import HTTPError

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
    """ Mocks requests.get method for two successful responses """

    def _mocked_requests_get(url, headers=None, params=None):
        mock_response = Mock()
        if params == {"perpage": 25, "page": 0}:
            mock_response.json.return_value = response_one_data
            mock_response.status_code = 200
            mock_response.headers = {'x-ratelimit-remaining': 119, 'x-ratelimit-limit': 120} 
        elif params == {"perpage": 25, "page": 1}:
            mock_response.json.return_value = response_two_data
            mock_response.status_code = 200
            mock_response.headers = {'x-ratelimit-remaining': 118, 'x-ratelimit-limit': 120} 
        else:
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = HTTPError("404 Client Error")
        return mock_response

    monkeypatch.setattr("requests.get", _mocked_requests_get)

@pytest.fixture
def mock_requests_get_no_status(monkeypatch):
    """ Mocks requests.get method without a status code """

    def _mocked_requests_get_no_status(url, headers=None, params=None):
        mock_response = Mock()
        return mock_response

    monkeypatch.setattr("requests.get", _mocked_requests_get_no_status)
