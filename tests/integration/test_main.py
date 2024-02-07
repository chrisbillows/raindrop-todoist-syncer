from datetime import datetime
import json
import os
import shutil
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch, Mock

import pytest
from requests import Response

from main import main
from raindrop import DatabaseManager, RaindropClient, RaindropsProcessor
import raindrop
from todoist import TodoistTaskCreator

from tests.conftest import mock_requests_get

# This returns a valid response object


@pytest.fixture
def mock_raindrops_data():
    with open("tests/mock_data/cumulative_rd_list.json") as f:
        return json.load(f)


@pytest.fixture
def mock_raindrop_client(mock_raindrops_data, monkeypatch):
    def mock_get_all_raindrops(self):
        return mock_raindrops_data

    def mock_valid_token(self):
        return True

    monkeypatch.setattr(RaindropClient, "get_all_raindrops", mock_get_all_raindrops)
    monkeypatch.setattr(RaindropClient, "stale_token", mock_valid_token)


@pytest.fixture
def mock_raindrops_processor(monkeypatch):
    def mock_newly_favourited_raindrops_extractor(self):
        return []

    monkeypatch.setattr(
        RaindropsProcessor,
        "newly_favourited_raindrops_extractor",
        mock_newly_favourited_raindrops_extractor,
    )


@pytest.fixture
def mock_todoist_creator(monkeypatch):
    def mock_create_task(self, task):
        pass

    # monkeypatch.setattr(TodoistTaskCreator, "create_task", mock_create_task)


class TestStaleTokenFunctionality:
    """
    Class to focus on testing the stale token functionality. Almost all of the remainder
    of the main function is mocked.
    """

    def test_working_test(self):
        assert 1 == 1

    @pytest.mark.skip(reason="this runs the stale token refresher for real!")
    def test_test_setup(
        self,
        mock_raindrop_client,
        mock_raindrops_processor,
        mock_todoist_creator,
        caplog,
    ):
        """
        Run-through to test mocks and monkey patches work correctly.
        main has no return hence x = main() - if main runs it will return None

        There are three "outputs" from main:
        a) all_raindrops
        b) tasks_to_create
        c) task_creator

        I had hoped just to mock all_raindrops and task_creator - but tasks to create
        writes to the db at the moment!
        """
        x = main()
        assert x == None

    @pytest.mark.skip(reason="this is prob fine but need to check")
    def test_invalid_token(
        self,
        mock_raindrop_client,
        mock_raindrops_processor,
        mock_todoist_creator,
        caplog,
    ):
        with patch(
            "raindrop.RaindropOauthHandler.refresh_token_process_runner"
        ) as mock_refresh_token_runner, patch(
            "raindrop.RaindropClient.stale_token", return_value=True
        ) as mock_valid_token:
            main()
            mock_refresh_token_runner.assert_called_once()

    @pytest.mark.skip(reason="this is also prob fine but need to check")
    def test_valid_token(
        self,
        mock_raindrop_client,
        mock_raindrops_processor,
        mock_todoist_creator,
        caplog,
    ):
        with patch(
            "raindrop.RaindropOauthHandler.refresh_token_process_runner"
        ) as mock_refresh_token_runner, patch(
            "raindrop.RaindropClient.stale_token", return_value=False
        ) as mock_valid_token:
            main()
            mock_refresh_token_runner.assert_not_called()


@pytest.fixture
def mock_db_data() -> dict[str, any]:
    """Creates the contents of a database file.

    Can be used in memory (as if read from the file) or written to a file and
    then read.

    Source of the data is an extracted API response using a set of real
    raindrops created for testing purposes (e.g. BBC News etc).

    Two items are removed, allowing the same test set to be used to introduce
    new, untracked raindrops.

    Can be used in conjunction with `mock_requests_get` which currently collects
    26 raindrops.  This database will hold 23 of those raindrops, leaving 3 "new"
    raindrops to be actioned.

    Returns
    -------
    mock_db_data: dict[str, any]
        A dictionary containing one item, the key "Processed Raindrops" and the
        value a list of raindrop dictionaries.

    See Also
    --------
    The return value can be used with `create_mock_db_files` to create a tempfile
    db and metafile data for most realistic use.
    """
    mock_db_data = {"Processed Raindrops": []}
    with open("tests/mock_data/rd_api_response_one.json") as f:
        full_api_response = json.load(f)
    mock_db_content = full_api_response["items"][:-2]
    mock_db_data["Processed Raindrops"] = mock_db_content
    return mock_db_data


# @pytest.fixture
# def mock_database_environment(monkeypatch, mock_db_data):
#     """A fixture to mock database/metafile attributes in a DatabaseManager object.

#     For dumb future me: pass this fixture as an argument to any test and
#     all DatabaseManager calls will be mocked to temp files.

#     The fixture creates temp directories for the db_file and meta_file. (The
#     programme uses the meta_file to track the latest version of the db json).

#     It uses `mock_db_data` to create the db content then calls
#     `create_mock_db_files` to write that db content to the files - with the
#     expected file formatting and metadata content.

#     `monkeypatch.setattr` uses pytest's monkeypatch to mock the DatabaseManager
#     attributes.

#     Yield is used to keep the method open, pending the required teardown at end
#     of test.

#     Teardown is performed by the shutil commands. (see notes below).

#     Parameters
#     ----------
#     monkeypatch
#         pytest generator that does some (as yet not understood) magic stuff.

#     mocked_db_data: dict[str, list]
#         Mock db data of the type created by `mock_db_data`

#     Notes
#     -----
#     This fixture is better written as:
#         `with tempfile.TemporaryDirectory() as db_dir...`
#     I used setattr for consistency across tests (see `mock_requests_get`). As part
#     of an effort to limit myself to a smaller set of testing tools and learn them
#     properly first. (Rather than every test being so different that "Dec-23 you"
#     found far too little knowledge consolidating.
#     """
#     db_dir = tempfile.mkdtemp()
#     meta_dir = tempfile.mkdtemp()
#     now = datetime.now().strftime("%Y%m%d_%H%M")

#     db_file_name = f"001_processed_raindrops_{now}.json"
#     meta_file_content = f"{meta_dir}/{db_file_name}"
#     # Metafile content format:
#     #   database/2391_processed_raindrops_20231231_0729.json

#     with open(os.path.join(db_dir, db_file_name), 'w') as f:
#         json.dump(mock_db_data, f)

#     with open(os.path.join(meta_dir, 'metafile.txt'), 'w') as f:
#         f.write(meta_file_content)

#     db_manager  = DatabaseManager()
#     monkeypatch.setattr(db_manager, 'database_directory', db_dir)
#     monkeypatch.setattr(db_manager, 'metafile_directory', meta_dir)
#     monkeypatch.setattr(db_manager, 'metafile_path', os.path.join(meta_dir, 'metafile.txt'))

#     yield

#     shutil.rmtree(db_dir)
#     shutil.rmtree(meta_dir)


class TestMainValid:
    """
    Full happy path integration test with the minimum amount of mocking.

    Includes individual tests for each mock used for traceability and clarity.

    DETAILS
    --------
    What does `main.main` do and how is mocking handled?

    1)  `main.main` confirms the Oauth token is not stale by making an API call using
        data in the .env file.

    - patched to return Oauth token is valid

    2) Fetches all raindrops from the raindrops api.

    #TODO:
    3) Extracts newly favourited raindrops.
    4) Compares them with the database and extracts 'new' favourites.
    5) Writes the new favourites to todoist.
    """

    def test_stale_token_patch(self):
        """Patches `stale_token` to directly return False.

        `stale_token` is a `RaindropClient()` method to test if the Oauth2 token is
        valid or needs refreshing.

        NOTE: This mock approach is not used in the integration test. See
        `test_stale_token_requests_patch` for the preferred approach.
        """
        rc = RaindropClient()
        with patch("raindrop.RaindropClient.stale_token", return_value=7):
            stale_token = rc.stale_token()
        assert stale_token == 7

    def test_stale_token_requests_patch(self, mock_requests_get):
        """Monkeypatches `requests.get` to assert `stale_token` is not true.

        For `stale_token` see `test_stale_token_patch`.

        Uses `mock_requests_get` to monkeypatch `stale_token`. P1 of the
        dummy data is returned by `mock_requests_get`. `stale_token` considers a token
        valid as long as `requests.get` doesn't raise an error. (It doesn't check
        status_code - but `mock_requests_get` does return valid status_codes if req'd).
        """
        rc = RaindropClient()
        stale_token = rc.stale_token()
        assert stale_token == False

    def test_get_all_rds(self, mock_requests_get):
        """Calls `get_all_rds` with a mock valid API response of 26 raindrops .

        `get_all_rds` is the primary RaindropClient() method.

        This test uses `mock_requests_get` to monkeypatch `requests.get`. Only the
        `.get` itself is mocked. Two valid pages of API response are returned
        and validated. `output` is list of 26 raindrops.

        `mock_requests_get` can be used directly in the full integration test.
        """
        rc = RaindropClient()
        output = rc.get_all_raindrops()
        assert len(output) == 26
        assert type(output) == list
        assert output[0]["title"] == "Hacker News"

    def test_newly_favourited_rd_extractor(self, mock_requests_get, mock_db_data, tmp_path):
        """
        `newly_favourited_rd_extractor` is the main RaindropsProcessor() method.
        #TODO: in progress. Working on. See issue for latest.
        """
        now = datetime.now().strftime("%Y%m%d_%H%M")
                
        # Create mock db
        db_dir = tmp_path / "database"
        db_file_name = f"001_processed_raindrops_{now}.json"
        db_dir.mkdir()
        with open(os.path.join(db_dir, db_file_name), "w") as f:
            json.dump(mock_db_data, f)

        # Create mock metafile
        meta_dir = tmp_path / "metafile"
        meta_file_content = f"{db_dir}/{db_file_name}"  #e.g. "database/2391_processed_raindrops_20231231_0729.json"
        meta_dir.mkdir()
        with open(os.path.join(meta_dir, "metafile.txt"), "w") as f:
            f.write(meta_file_content)

        with patch.object(
            DatabaseManager, '__init__', lambda self: self.__dict__.update(
                {
            "database_directory": str(db_dir),
            "metafile_directory": str(meta_dir),
            "metafile_path": os.path.join(meta_dir, 'metafile.txt')
                }
                )
            ) as mock_init:
        
            rc = RaindropClient()
            # Get mock API response of 26 raindrops
            output = rc.get_all_raindrops()
            assert len(output) == 26

            # Instantiate rp with the 26 raindrops
            rp = RaindropsProcessor(output)

            # Process 26 raindrops against 23 in mock database
            new_rds_found = rp.newly_favourited_raindrops_extractor()

            assert len(new_rds_found) == 0

    # @pytest.mark.skip(message="Not finished yet")
    def test_happy_path(self, mock_requests_get):
        """
        #TODO: in progress
        Currently illustrates `mock_requests_get` successfully monkeypatching
        `requests.get` in two seperate function calls.
        """
        rc = RaindropClient()
        stale_token = rc.stale_token()
        output = rc.get_all_raindrops()
        assert stale_token == False
        assert len(output) == 26
