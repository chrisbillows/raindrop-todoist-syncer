import json
from unittest.mock import patch

import pytest

from raindrop_todoist_syncer.rd_process import RaindropsProcessor
from raindrop_todoist_syncer.rd_class import Raindrop


@pytest.fixture
def rd_processor():
    """
    A dummy JSON equivalent to the list of dicts extracted by the get_all_raindrops
    method of the RaindropsClient. i.e. this is the expected data the driver method of
    RaindropsProcessor works with.
    """
    with open("tests/mock_data/cumulative_rd_list.json", "r") as f:
        cumulative_rds = json.load(f)
    return RaindropsProcessor(cumulative_rds)


@pytest.fixture
def dummy_all_favs(rd_processor):
    """
    A subset of the rds passed into the rd_processor fixture. A list of all the
    favourited rds in the dummy data - which, with the current data set, is one
    favourited rd.
    """
    all_favs = [rd for rd in rd_processor.all_rds if rd.get("important")]
    return all_favs


class TestRaindropProcessorInit:
    def test_basic_init(self, rd_processor):
        with open("tests/mock_data/cumulative_rd_list.json", "r") as f:
            cumulative_rds = json.load(f)
        assert rd_processor.all_rds == cumulative_rds


class TestMainFunction:
    """
    You could now replace instantiating rd_processor with the rd_processor fixture.
    BUT you must leave it as is.  As a reminder that I don't need to excruciatingly
    fiddle with every single thing! LIVE WITH THIS AS IT IS!
    """

    @patch("raindrop_todoist_syncer.rd_process.DatabaseManager")
    def test_newly_favourited_raindrops_exctractor(self, MockDatabaseManager):
        mock_db_return_value = {
            "Processed Raindrops": [
                {"id": 1, "title": "Some Title"},
                {"id": 2, "title": "Some other Title"},
            ]
        }
        MockDatabaseManager.return_value.get_latest_database.return_value = (
            mock_db_return_value
        )
        with open("tests/mock_data/cumulative_rd_list.json", "r") as f:
            all_rds = json.load(f)
        rd_processor = RaindropsProcessor(all_rds)
        rd_objects = rd_processor.newly_favourited_raindrops_extractor()
        assert len(rd_objects) == 1


class TestExtractAllFavRds:
    """
    Don't parametrize due to length of input / output.
    """

    def test_extract_all_fav_rds_dummy_data(self, rd_processor):
        new_fav_rds = rd_processor._extract_all_fav_rds()
        assert len(new_fav_rds) == 1 and new_fav_rds[0]["_id"] == 628161667

    def test_extract_all_fav_rds_two_of_three(self):
        all_rds = [
            {"_id": 1, "important": True},
            {"_id": 2, "important": True},
            {"_id": 3},
        ]
        rdp = RaindropsProcessor(all_rds)
        new_fav_rds = rdp._extract_all_fav_rds()
        assert new_fav_rds == [
            {"_id": 1, "important": True},
            {"_id": 2, "important": True},
        ]

    def test_extract_all_fav_rds_none(self):
        all_rds = [
            {"_id": 1},
            {"_id": 2},
            {"_id": 3},
        ]
        rdp = RaindropsProcessor(all_rds)
        new_fav_rds = rdp._extract_all_fav_rds()
        assert new_fav_rds == []

    def test_extact_all_fav__rds_empty(self):
        all_rds = []
        rdp = RaindropsProcessor(all_rds)
        new_fav_rds = rdp._extract_all_fav_rds()
        assert new_fav_rds == []


class TestFetchTrackedFavs:
    @patch("raindrop_todoist_syncer.rd_process.DatabaseManager")
    def test_fetch_tracked_favs(self, MockDatabaseManager):
        mock_db_return_value = {
            "Processed Raindrops": [
                {"id": 1, "Title": "Some Title"},
                {"id": 2, "Title": "Some other Title"},
            ]
        }
        MockDatabaseManager.return_value.get_latest_database.return_value = (
            mock_db_return_value
        )
        rdp = RaindropsProcessor([])
        tracked_favs = rdp._fetch_tracked_favs()
        tracked_fav_ids = {rd["id"] for rd in tracked_favs}
        assert tracked_fav_ids == {1, 2}


class TestExtractUntrackedFavs:
    def test_extract_untracked_dummy_id_not_tracked(self, rd_processor, dummy_all_favs):
        tracked_favs = [{"id": 123456789}]
        untracked_favs = rd_processor._extract_untracked_favs(
            dummy_all_favs, tracked_favs
        )
        print(untracked_favs)
        assert untracked_favs[0]["_id"] == 628161667

    def test_extract_untracked_favs_dummy_seen_before(
        self, rd_processor, dummy_all_favs
    ):
        tracked_favs = [{"id": 628161667}]
        untracked_favs = rd_processor._extract_untracked_favs(
            dummy_all_favs, tracked_favs
        )
        assert untracked_favs == []

    def test_extract_untracked_favs_three_new_three_seen(self):
        tracked_favs = [{"id": 123}, {"id": 789}, {"id": 131415}]
        all_favs = [
            {"_id": 123, "title": "Title 1"},
            {"_id": 456, "title": "Title 2"},
            {"_id": 789, "title": "Title 3"},
            {"_id": 101112, "title": "Title 4"},
            {"_id": 131415, "title": "Title 5"},
            {"_id": 161718, "title": "Title 6"},
        ]
        rdp = RaindropsProcessor(all_favs)
        untracked_favs = rdp._extract_untracked_favs(all_favs, tracked_favs)
        untracked_favs_ids = {rd["_id"] for rd in untracked_favs}
        assert untracked_favs_ids == {456, 101112, 161718}

    def test_extract_untracked_favs_three_seen(self):
        tracked_favs = [{"id": 123}, {"id": 456}, {"id": 789}]
        all_favs = [
            {"_id": 123, "title": "Title 1"},
            {"_id": 456, "title": "Title 2"},
            {"_id": 789, "title": "Title 3"},
        ]
        rdp = RaindropsProcessor(all_favs)
        untracked_favs = rdp._extract_untracked_favs(all_favs, tracked_favs)
        assert untracked_favs == []

    def test_extract_untracked_favs_none_tracked(self):
        tracked_favs = []
        all_favs = [
            {"_id": 123, "title": "Title 1"},
            {"_id": 456, "title": "Title 2"},
            {"_id": 789, "title": "Title 3"},
        ]
        rdp = RaindropsProcessor(all_favs)
        untracked_favs = rdp._extract_untracked_favs(all_favs, tracked_favs)
        untracked_favs_ids = {rd["_id"] for rd in untracked_favs}
        assert untracked_favs_ids == {123, 456, 789}


class TestConvertToRdObjects:
    @pytest.fixture
    def dummy_mock_fav(self):
        with open("tests/mock_data/cumulative_rd_list.json", "r") as f:
            all_rds = json.load(f)
        fav = [rd for rd in all_rds if rd.get("important")]
        return RaindropsProcessor([])._convert_to_rd_objects(fav)

    def test_is_instance_of_raindrop_dummy(self, dummy_mock_fav):
        assert isinstance(dummy_mock_fav[0], Raindrop)

    def test_has_correct_title_dummy(self, dummy_mock_fav):
        assert (
            dummy_mock_fav[0].title
            == "Amazon.co.uk: Low Prices in Electronics, Books, Sports Equipment & more"
        )

    def test_has_correct_id_dummy(self, dummy_mock_fav):
        assert dummy_mock_fav[0].id == 628161667

    def test_has_correct_created_date_dummy(self, dummy_mock_fav):
        assert dummy_mock_fav[0].created_time == "2023-08-14T09:36:24.851Z"

    def test_has_correct_note_dummy(self, dummy_mock_fav):
        assert dummy_mock_fav[0].notes == "Test note"

    def test_has_correct_link_dummy(self, dummy_mock_fav):
        assert dummy_mock_fav[0].link == "https://www.amazon.co.uk/"

    @pytest.fixture
    def marty_mock_fav(self):
        fav = [
            {
                "_id": 123,
                "created": "1955-11-05T01:24:00.111Z",
                "parsed_time": "1955-11-05T01:24:00.111Z",
                "title": "Marty! You gotta come back with me!",
                "note": "Back where?",
                "link": "www.backtothefuture!.com",
            }
        ]
        return RaindropsProcessor(fav)._convert_to_rd_objects(fav)

    def test_is_instance_of_raindrop_marty(self, marty_mock_fav):
        assert isinstance(marty_mock_fav[0], Raindrop)

    def test_has_correct_title_marty(self, marty_mock_fav):
        assert marty_mock_fav[0].title == "Marty! You gotta come back with me!"

    def test_has_correct_id_marty(self, marty_mock_fav):
        assert marty_mock_fav[0].id == 123

    def test_has_correct_created_date_marty(self, marty_mock_fav):
        assert marty_mock_fav[0].created_time == "1955-11-05T01:24:00.111Z"

    def test_has_correct_note_marty(self, marty_mock_fav):
        assert marty_mock_fav[0].notes == "Back where?"

    def test_has_correct_link_marty(self, marty_mock_fav):
        assert marty_mock_fav[0].link == "www.backtothefuture!.com"

    def test_empty_list(self):
        fav = []
        rdp = RaindropsProcessor(fav)
        rd_objects = rdp._convert_to_rd_objects(fav)
        assert rd_objects == []

    # TODO - Raindrop class has no error handling for
    @pytest.mark.skip(
        reason="Known issue: Raindrop class will crash in event of a missing field."
    )
    def test_id_field_missing(self):
        fav = [
            {
                "created": "1955-11-05T01:24:00.111Z",
                "parsed_time": "1955-11-05T01:24:00.111Z",
                "title": "Marty! You gotta come back with me!",
                "note": "Back where?",
                "link": "www.backtothefuture!.com",
            }
        ]
        rdp = RaindropsProcessor(fav)
        rd_objects = rdp._convert_to_rd_objects(fav)
        assert rd_objects == []
