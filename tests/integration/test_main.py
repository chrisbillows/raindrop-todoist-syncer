from datetime import datetime
import json
import os
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from raindrop_todoist_syncer.main import main
from raindrop_todoist_syncer.raindrop import (
    DatabaseManager,
    RaindropClient,
)
from raindrop_todoist_syncer.rd_process import RaindropsProcessor
from raindrop_todoist_syncer.todoist import TodoistTaskCreator


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
        assert x is None

    @pytest.mark.skip(reason="this is prob fine but need to check")
    def test_invalid_token(
        self,
        mock_raindrop_client,
        mock_raindrops_processor,
        mock_todoist_creator,
        caplog,
    ):
        with patch(
            "raindrop.RaindropAccessTokenRefresher.refresh_token_process_runner"
        ) as mock_refresh_token_runner, patch(
            "raindrop.RaindropClient.stale_token", return_value=True
        ) as mock_valid_token:  # noqa
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
            "raindrop.RaindropAccessTokenRefresher.refresh_token_process_runner"
        ) as mock_refresh_token_runner, patch(
            "raindrop.RaindropClient.stale_token", return_value=False
        ) as mock_valid_token:  # noqa
            main()
            mock_refresh_token_runner.assert_not_called()


@pytest.fixture
def DELETE_ME_mock_db_data() -> dict[str, any]:
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

    1)  It confirms the Oauth token is not stale by making an API call using
        data in the .env file.

    See: `test_stale_token_requests_patch` (`test_stale_token_patch` is an alternative)

    2)  It fetches all raindrops from the raindrops api.

    See: `test_get_all_rds`

    3)  It extracts newly favourited raindrops. And it compares them with the database
        and extracts 'new' favourites.

    See: `test_newly_favourited_rd_extractor`

    4) Writes the new favourites to todoist.

    See:
    """

    def test_stale_token_patch(self):
        """Patches `stale_token` to directly return False.

        `stale_token` is a `RaindropClient()` method to test if the Oauth2 token is
        valid or needs refreshing.

        NOTE: This mock approach is not used in the integration test. See
        `test_stale_token_requests_patch` for the preferred approach.
        """
        rc = RaindropClient()
        with patch(
            "raindrop_todoist_syncer.raindrop.RaindropClient.stale_token",
            return_value=7,
        ):
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
        assert not stale_token

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
        assert isinstance(output, list)
        assert output[0]["title"] == "Hacker News"

    def test_newly_favourited_rd_extractor(
        self, mock_requests_get, mock_db_contents, tmp_path
    ):
        """Calls `newly_favourited_rd_extractor` and extracts two untracked favourites.

        `newly_favourited_rd_extractor` is the main `RaindropsProcessor()` method.

        This test creates temp database and metadata files. The temp database uses the
        data in the `mock_db` fixture. The temp files are created with pytest's
        `tmp_path` for automatic teardown.

        The test uses unittest patch to mock the hardcoded `__init__` values in a
        `DatabaseManager` instance, redirecting to the temp db and metafile. All other
        `DatabaseManager` class methods function as normal.

        `output` is a mock of a processed API output. The source is `mock_requests_get`
        and that combined api responses is processed by
        `RaindropClient.get_all_raindrops()`.

        The *Act* section of the test is the last two lines before the assert. An
        instance of `RaindropsProcessor` is instantiated with the dummy API response.
        `newly_favourited_raindrops_extractor` is run on the API response.

        Twenty six raindrops are passed. Three favourites are found and checked against
        the `mock_db` loaded from the temp file, which contains one favourite.

        Two new and untracked favourites are returned (The Times and Amazon).
        """
        now = datetime.now().strftime("%Y%m%d_%H%M")

        # Create mock db
        db_dir = tmp_path / "database"
        db_file_name = f"001_processed_raindrops_{now}.json"
        db_dir.mkdir()
        with open(os.path.join(db_dir, db_file_name), "w") as f:
            json.dump(mock_db_contents, f)

        # Create mock metafile
        meta_dir = tmp_path / "metafile"
        meta_file_content = f"{db_dir}/{db_file_name}"  # e.g. "database/2391_processed_raindrops_20231231_0729.json"
        meta_dir.mkdir()
        with open(os.path.join(meta_dir, "metafile.txt"), "w") as f:
            f.write(meta_file_content)

        with patch.object(
            DatabaseManager,
            "__init__",
            lambda self: self.__dict__.update(
                {
                    "database_directory": str(db_dir),
                    "metafile_directory": str(meta_dir),
                    "metafile_path": os.path.join(meta_dir, "metafile.txt"),
                }
            ),
        ) as mock_init:  # noqa F841
            # Uses RaindropClient() to extract data from the mock API files rather than
            # just loading the data directly because:
            #   a) use the consolidated two pages of API response provided by
            #      `mock_requests_get`
            #   b) ensures exact formatting correct e.g. dict that starts with
            #      "Raindrops processed" vs. just the list of dicts etc.
            rc = RaindropClient()

            # Get mock API response of 26 raindrops / 3 favourites
            output = rc.get_all_raindrops()
            assert len(output) == 26

            # Instantiate rp with the 26 raindrops / 3 favourites
            # Process against db with 1 existing favourite
            rp = RaindropsProcessor(output)
            new_favs_found = rp.newly_favourited_raindrops_extractor()

            assert len(new_favs_found) == 2

    def test_task_creation(self, raindrop_object):
        """Creates a mock task from a Raindrop using `TodoistTaskCreator.create_task().`

        `main.py` creates a list of untracked Raindrops called `tasks_to_create`. A for
        `TodoistTaskCreator.create_task().` then creates a task for each untracked
        Raindrop via a for loop in `main.py`.

        This test uses the mock Raindrop fixture `raindrop_object` as `tasks_to_create`.
        The test then mocks the Todoist API methods `add_task` and `add_comment` and
        patches those methods when instantiating a TodoistTaskCreator object.
        # mock raindrop

        The test asserts that the mock methods were correctly called with the data from
        the mock Raindrop `raindrop_object`.
        """
        untracked_raindrop_object_mock = raindrop_object

        # mock of TodoistAPI response required by `_add_link_as_comment`
        mock_task_response_object = Mock()
        mock_task_response_object.id = "dummy_id"
        mock_task_response_object.title = "Dummy Title"

        # patch todoist API methods - not my TodoistTaskCreator class methods.
        with patch(
            "todoist_api_python.api.TodoistAPI.add_task",
            return_value=mock_task_response_object,
        ) as mock_add_task, patch(
            "todoist_api_python.api.TodoistAPI.add_comment"
        ) as mock_add_comment:  # noqa F841
            # create task
            task_creator = TodoistTaskCreator(untracked_raindrop_object_mock)
            task_creator.create_task()

            # assertions
            mock_add_task.assert_called()  # This just checks the method was called
            called_args, called_kwargs = mock_add_task.call_args

            # Can use ``assert_called_once_with` but kept individual for future ref
            assert called_kwargs.get("content") == "Welcome to Python.org"
            assert called_kwargs.get("project_id") == "2314091414"
            assert called_kwargs.get("description") == ""
            assert called_kwargs.get("due_string") == "today"
            assert called_kwargs.get("due_lang") == "en"
            assert called_kwargs.get("priority") == 1
            assert called_kwargs.get("labels") == ["Raindrop"]

    def test_database_write(self, mock_db_contents, raindrop_object, tmp_path):
        """Writes a Raindrop object to an existing database.

        `main.py` creates a list of untracked Raindrops called `tasks_to_create`.
        `TodoistTaskCreator.create_task().` creates a task for each untracked
        Raindrop via a for loop in `main.py`. The loop then updates the database with
        the new Raindrop.

        This test creates temp database and metadata files. The temp database uses the
        data in the `mock_db` fixture. The temp files are created with pytest's
        `tmp_path` for automatic teardown.

        The test uses unittest patch to mock the hardcoded `__init__` values in a
        `DatabaseManager` instance, redirecting to the temp db and metafile. All other
        `DatabaseManager` class methods function as normal.

        This test uses the single mock Raindrop `raindrop_object` as `tasks_to_create`.

        The test then makes assertions against a) the original database b) the newly
        updated database.

        The database should being containing one Raindrop and end containg two
        Raindrops.
        """
        now = datetime.now().strftime("%Y%m%d_%H%M")

        # Create mock db
        db_dir = tmp_path / "database"
        db_file_name = f"001_processed_raindrops_{now}.json"
        db_dir.mkdir()
        with open(os.path.join(db_dir, db_file_name), "w") as f:
            json.dump(mock_db_contents, f)

        # Create mock metafile
        meta_dir = tmp_path / "metafile"
        meta_file_content = f"{db_dir}/{db_file_name}"  # e.g. "database/2391_processed_raindrops_20231231_0729.json"
        meta_dir.mkdir()
        with open(os.path.join(meta_dir, "metafile.txt"), "w") as f:
            f.write(meta_file_content)

        task = raindrop_object

        with patch.object(
            DatabaseManager,
            "__init__",
            lambda self: self.__dict__.update(
                {
                    "database_directory": str(db_dir),
                    "metafile_directory": str(meta_dir),
                    "metafile_path": os.path.join(meta_dir, "metafile.txt"),
                }
            ),
        ) as mock_init:  # noqa F841
            dbm = DatabaseManager()
            current_rds = dbm.get_latest_database()["Processed Raindrops"]

            dbm.update_database([task])
            updated_rds = dbm.get_latest_database()["Processed Raindrops"]

            print(current_rds)
            print(updated_rds)

            assert raindrop_object.title == "Welcome to Python.org"
            assert current_rds[0]["title"] == "Hacker News"
            assert updated_rds[0]["title"] == "Hacker News"
            assert updated_rds[1]["title"] == "Welcome to Python.org"
            assert len(updated_rds) == len(current_rds) + 1

    def test_main_happy_path_unabridged(
        self, mock_requests_get, mock_db_contents, tmp_path
    ):
        """Integration test for main, with the main imported by hand, copying over
        it's individual calls, line by line.

        This skeletal approach brought together the mocks created function call by
        function call in this test class.

        It is kept to aid future deicphering.

        See `test_main_happy_path` for the full integration test and an extensive
        docstring.

        NOTE: This test doesn't not include the database write but is covered in
        `test_main_happy_path`.
        """
        now = datetime.now().strftime("%Y%m%d_%H%M")

        # Create mock db
        db_dir = tmp_path / "database"
        db_file_name = f"001_processed_raindrops_{now}.json"
        db_dir.mkdir()
        with open(os.path.join(db_dir, db_file_name), "w") as f:
            json.dump(mock_db_contents, f)

        # Create mock metafile
        meta_dir = tmp_path / "metafile"
        meta_file_content = f"{db_dir}/{db_file_name}"  # e.g. "database/2391_processed_raindrops_20231231_0729.json"
        meta_dir.mkdir()
        with open(os.path.join(meta_dir, "metafile.txt"), "w") as f:
            f.write(meta_file_content)

        # mock of TodoistAPI response required by `_add_link_as_comment`
        # every task created will have the same id/title
        mock_task_response_object = Mock()
        mock_task_response_object.id = "dummy_id"
        mock_task_response_object.title = "**Dummy Title**"

        # patch 1) TodoistAPI.add_task
        # patch 2) TodoistAPI.add_comment
        # patch 3) DatabaseManager.__init__.database_directory etc.
        with patch(
            "todoist_api_python.api.TodoistAPI.add_task",
            return_value=mock_task_response_object,
        ) as mock_add_task, patch(
            "todoist_api_python.api.TodoistAPI.add_comment"
        ) as mock_add_comment, patch.object(  # noqa F841
            DatabaseManager,
            "__init__",
            lambda self: self.__dict__.update(
                {
                    "database_directory": str(db_dir),
                    "metafile_directory": str(meta_dir),
                    "metafile_path": os.path.join(meta_dir, "metafile.txt"),
                }
            ),
        ) as mock_init:  # noqa F841
            raindrop_client = RaindropClient()

            # mock_requests_get monkeypatches `requests.get` with valid data.
            # a) stale token returns False
            # b) `all raindrops` is a list
            if raindrop_client.stale_token():
                print("oh shit")
            all_raindrops = raindrop_client.get_all_raindrops()

            # assert mock_requests_get monkeypatch is working
            assert not raindrop_client.stale_token()
            assert len(all_raindrops) == 26

            # with `patch.object` redirects hardcoded `__init__` values in a
            # `DatabaseManager` instance, redirecting to the temp db and metafile.
            raindrops_processor = RaindropsProcessor(all_raindrops)
            tasks_to_create = raindrops_processor.newly_favourited_raindrops_extractor()

            # assert patch.object is working
            assert len(tasks_to_create) == 2

            for task in tasks_to_create:
                task_creator = TodoistTaskCreator(task)
                task_creator.create_task()

            # assert `add_task` was called twice
            assert len(mock_add_task.call_args_list) == 2

            # assert content of calls
            x_args, x_kwargs = mock_add_task.call_args_list[0]
            y_args, y_kwargs = mock_add_task.call_args_list[1]

            assert x_kwargs["project_id"] == "2314091414"
            assert (
                x_kwargs["content"]
                == "The Times & The Sunday Times: breaking news & today's latest headlines"
            )
            assert (
                y_kwargs["content"]
                == "Amazon.co.uk: Low Prices in Electronics, Books, Sports Equipment & more"
            )

    def test_main_happy_path(self, mock_requests_get, mock_db_contents, tmp_path):
        """Integration test for main.

        This tests consolidates together the mocks built up for individual parts of the
        main function in `TestMainValid`.

        The fixture `mock_requests_get` uses monkeypatch to mock any `requests.get`
        call made in the entire test. `mock_requests_get` returns two pages of
        valid Raindrop.io API response containing a total of 26 raindrops.  Three of
        those raindrops are favourited (k: "important", v: "true").

        Of those three favourites, one ("Hacker News") already exists in the
        `mock_db_contents` fixture.

        Therefore the test should produce two newly favourite raindrops: "The Times"
        and "Amazon"

        The test itself initially arranges:

        a) a mock database json file: a tmp file in a tmp directory, using pytests's
           `tmp_path` for automatic teardown. The database is written from the
           `mock_db_contents` fixture which reads in "tests/mock_data/mock_db.json".

           `mock_db_contents` contains one processed Raindrop: Hacker News. (This
           favourite exists in the Raindrop.io API response provided by
           `mock_requests.get`).

        b) a mock temp file to provide the location of the "mock_db.json".

        c) a Mock Todoist.Task API response (which is required by `add_link_as_comment`)

        The test then calls `main.py` using a `with` context managing applying unittest
        patches to:

        1) `TodoistAPI.add_task`: a patch for the API call which returns the Mock
           Todoist Task object.

        2) `TodoistAPI.add_comment`: A patch for the API call. No return is specified.

        3) `DatabaseManager.__init__`: A patch for the `__init__`` method of any
            instance of `DatabaseManager`.  The patch overwrites the location the
            real location of the database directory, metafile directory and metafile.
            They are replaced with paths to their temp equivalents.

        Assertions
        ----------
        The assertions utilise  `call_args_list` to assert that multiple calls to
        the mocked Todoist.API.create_task endpoint were made correctly.

        Assertions check the newly found Raindrops are correctly written to the temp
        directory files using Pathlib. The files in the temp database directory are
        listed and the number of files are checked.  Then the title of the newest
        entry in the database is checked against the expected list.
        """

        now = datetime.now().strftime("%Y%m%d_%H%M")

        # Create mock db
        db_dir = tmp_path / "database"
        db_file_name = f"001_processed_raindrops_{now}.json"
        db_dir.mkdir()
        with open(os.path.join(db_dir, db_file_name), "w") as f:
            json.dump(mock_db_contents, f)

        # Create mock metafile
        meta_dir = tmp_path / "metafile"
        meta_file_content = f"{db_dir}/{db_file_name}"  # e.g. "database/2391_processed_raindrops_20231231_0729.json"
        meta_dir.mkdir()
        with open(os.path.join(meta_dir, "metafile.txt"), "w") as f:
            f.write(meta_file_content)

        # mock of TodoistAPI response required by `_add_link_as_comment`
        # every task created will have the same id/title
        mock_task_response_object = Mock()
        mock_task_response_object.id = "dummy_id"
        mock_task_response_object.title = "**Dummy Title**"

        # patch 1) TodoistAPI.add_task
        # patch 2) TodoistAPI.add_comment
        # patch 3) DatabaseManager.__init__.database_directory etc.
        with patch(
            "todoist_api_python.api.TodoistAPI.add_task",
            return_value=mock_task_response_object,
        ) as mock_add_task, patch(
            "todoist_api_python.api.TodoistAPI.add_comment"
        ) as mock_add_comment, patch.object(  # noqa F841
            DatabaseManager,
            "__init__",
            lambda self: self.__dict__.update(
                {
                    "database_directory": str(db_dir),
                    "metafile_directory": str(meta_dir),
                    "metafile_path": os.path.join(meta_dir, "metafile.txt"),
                }
            ),
        ) as mock_init:  # noqa F841
            main()

            # assert `add_task` was called twice
            assert len(mock_add_task.call_args_list) == 2

            # assert content of calls
            x_args, x_kwargs = mock_add_task.call_args_list[0]
            y_args, y_kwargs = mock_add_task.call_args_list[1]

            assert x_kwargs["project_id"] == "2314091414"
            assert (
                x_kwargs["content"]
                == "The Times & The Sunday Times: breaking news & today's latest headlines"
            )
            assert (
                y_kwargs["content"]
                == "Amazon.co.uk: Low Prices in Electronics, Books, Sports Equipment & more"
            )

            # assert contents of database
            db_path = Path(db_dir)
            db_files = list(db_path.iterdir())
            newest_items = []
            # reads the path from each Path object, loads the JSON and captures
            # the title in a list.
            for file in db_files:
                with open(str(file), "r") as f:
                    content = json.load(f)
                    newest_item_title = content["Processed Raindrops"][-1]["title"]
                    print(newest_item_title)
                    newest_items.append(newest_item_title)

            assert len(db_files) == 3
            # assert the correct three titles are present in the list.
            # `in` is used because the list order is not consistent.
            assert "Hacker News" in newest_items
            assert (
                "The Times & The Sunday Times: breaking news & today's latest headlines"
                in newest_items
            )
            assert (
                "Amazon.co.uk: Low Prices in Electronics, Books, Sports Equipment & more"
                in newest_items
            )
