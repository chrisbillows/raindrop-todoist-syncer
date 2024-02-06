from datetime import datetime
import json
import os
import shutil
import tempfile
from typing import Any
from unittest.mock import patch, Mock

import pytest
from requests import Response

from main import main
from raindrop import DatabaseManager, RaindropClient, RaindropsProcessor
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

    def test_invalid_token(
        self,
        mock_raindrop_client,
        mock_raindrops_processor,
        mock_todoist_creator,
        caplog,
    ):
        with patch("raindrop.RaindropOauthHandler.refresh_token_process_runner") as mock_refresh_token_runner, patch(
            "raindrop.RaindropClient.stale_token",
            return_value = True
        ) as mock_valid_token:
            main()
            mock_refresh_token_runner.assert_called_once()

    def test_valid_token(
        self,
        mock_raindrop_client,
        mock_raindrops_processor,
        mock_todoist_creator,
        caplog,
    ):
        with patch("raindrop.RaindropOauthHandler.refresh_token_process_runner") as mock_refresh_token_runner, patch(
            "raindrop.RaindropClient.stale_token",
            return_value = False
        ) as mock_valid_token:
            main()
            mock_refresh_token_runner.assert_not_called()


class TestMainValidReturns:
    """
    Full integration tests with the minimum amount of mocking. Series of tests 
    validating steps on the happy path.
    
    - Uses real.env and assumes a non-stale token
        - mocks the api response & the database used
           - api finds one new raindrop
        - rds processed for real
        - `tasks_to_create` created for real
    
    - Writes to mock database 
     """
        
    def mock_db_data(self) -> dict[str, any]:
        """Creates the contents of a database file. 
        
        Can be used in memory (as if read from the file) or written to a file and 
        then read.
        
        Source of the data is an extracted API response using a set of real 
        raindrops created for testing purposes (e.g. BBC News etc).
        
        Two items are removed, allowing the same test set to be used to introduce
        new, untracked raindrops.
        
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
        mock_db_data = {
            "Processed Raindrops": [
                ]
        }
        with open("tests/mock_data/rd_api_response_one.json") as f:
            full_api_response = json.load(f)
        mock_db_content = full_api_response["items"][:-2]
        mock_db_data["Processed Raindrops"] = mock_db_content
        return mock_db_data
    
    def create_mock_db_files(self, directory: str, filename: str, content: dict[str, list]) -> None:
        """Creates a mock_db file and accompanying metafile.
        
        Parameters
        ----------
        directory: str
            The path to the directory to save the mock_db file.
        
        filename: str
            The name for the file e.g. the db file and metafile (which must be in a 
            particular format).
        
        content: dict[str, list]
            The content of the database. To be valid this should be in the format of
            one k,v pair with a key of "Processed Raindrops" and the saved raindrop 
            content as a list of dictionaries.
        
        Note
        ----
        This method could be used to create any file - but for ease of future me's
        understanding, I've described it's specific use in `mock_database_env`.
        """
        
        with open(os.path.join(directory, filename), 'w') as file:
            file.write(content)
            #! CHAT GPT says this will error a dict
            #! prob getting this from my type annotations - which may be wrong! 
            # json.dump(content, file)
        return None

    @pytest.fixture
    def mock_database_env(self, monkeypatch, mocked_db_data):
        """A fixture to mock database/metafile attributes in a DatabaseManager object.
        
        For dumb future me: pass this fixture as an argument to any test and 
        all DatabaseManager calls will be mocked to temp files. 
        
        The fixture creates temp directories for the db_file and meta_file. (The 
        programme uses the meta_file to track the latest version of the db json).
        
        It uses `mock_db_data` to create the db content then calls 
        `create_mock_db_files` to write that db content to the files - with the
        expected file formatting and metadata content.
        
        `monkeypatch.setattr` uses pytest's monkeypatch to mock the DatabaseManager
        attributes. 
        
        Yield is used to keep the method open, pending the required teardown at end
        of test.
        
        Teardown is performed by the shutil commands. (see notes below).
       
        Parameters
        ----------
        monkeypatch
            pytest generator that does some (as yet not understood) magic stuff.
        
        mocked_db_data: dict[str, list]
            Mock db data of the type created by `mock_db_data` 
               
        Notes
        -----
        This fixture is better written as: 
            `with tempfile.TemporaryDirectory() as db_dir...`
        I used setattr for consistency across tests (see `mock_requests_get`). As part 
        of an effort to limit myself to a smaller set of testing tools and learn them
        properly first. (Rather than every test being so different that "Dec-23 you" 
        found far too little knowledge consolidating.
        """
        db_dir = tempfile.mkdtemp()
        meta_dir = tempfile.mkdtemp()
        
        now = datetime.now()
        now_formatted = now.strftime("%Y%m%d_%H%M")
        
        db_file_name = f"001_processed_raindrops_{now_formatted}.json"
        meta_file_content = f"{meta_dir}/{db_file_name}.json"
        # Metafile content format:
        #   database/2391_processed_raindrops_20231231_0729.json
        
        self.create_mock_db_files(db_dir, db_file_name, mocked_db_data)
        self.create_mock_db_files(meta_dir, 'metafile.txt', meta_file_content)

        monkeypatch.setattr(DatabaseManager, 'database_directory', db_dir)
        monkeypatch.setattr(DatabaseManager, 'metafile_directory', meta_dir)
        monkeypatch.setattr(DatabaseManager, 'metafile_path', os.path.join(meta_dir, 'metafile.txt'))
         
        yield
        
        shutil.rmtree(db_dir)
        shutil.rmtree(meta_dir)
        
        #! NEXT - re-read this and check through, then run some bit by bit tests 
        #! below.
         
    # @patch('todoist.TodoistTaskCreator')
    #def test_valid_return(self, mock_requests_get):
    def test_valid_return(self):
        """
        - Uses real.env and assumes a non-stale token
        - Uses mock_requests_get which is a valid response object
        - mocks the api response & the database used
           - api finds one new raindrop
        - rds processed for real
        - `tasks_to_create` created for real
        - 
        """
        # Arrange
        ## 1 - need a mock database
        ## 2 - need to be able "write" to the new database file
        ## 3 - mock API response with two new rds
        ## 4 - monkeypatch the todoist_api call
                
        ### a) Make a database out of rd_api_response_one minus TWO rds
        ### b) Make the API response out of ALL of rd_api_response
        
        # MockTodoistTaskCreator.return_value.create_task.return_value = None

              
        
        
        # Act
        ##actual = main()
        
        # Assert
        assert now_formatted == 1
        
    
    
