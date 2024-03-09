class TestInit:
    """
    Early warning system for my own idiocy.
    """

    def test_init_id(self, raindrop_object):
        assert raindrop_object.id == 628161672

    def test_init_created_time(self, raindrop_object):
        assert raindrop_object.created_time == "2023-08-14T09:36:24.856Z"

    def test_parsed_date_not_none(self, raindrop_object):
        assert raindrop_object.parsed_time is not None

    def test_init_title(self, raindrop_object):
        assert raindrop_object.title == "Welcome to Python.org"

    def test_init_notes(self, raindrop_object):
        assert raindrop_object.notes == ""

    def test_init_link(self, raindrop_object):
        assert raindrop_object.link == "https://www.python.org/"


class TestToDict:
    def test_to_dict(self, raindrop_object):
        raindrop_object.parsed_time = "2023-08-01T01:01:01.001Z"
        expected_result = {
            "id": 628161672,
            "created_time": "2023-08-14T09:36:24.856Z",
            "parsed_time": "2023-08-01T01:01:01.001Z",
            "title": "Welcome to Python.org",
            "notes": "",
            "link": "https://www.python.org/",
        }
        assert raindrop_object.to_dict() == expected_result


class TestInitErrors:
    """
    Test object for handling possible edge case data returned from the API.
    """

    def tests_init_no_id(self, raindrop_object):
        pass


"""
RD OBJECT EXAMPLE
    {
        "id": 588482518,
        "created_time": "2023-06-09T14:45:58.831Z",
        "parsed_time": "2023-06-14T16:10:14.085+00:00",
        "title": "How to Write Unit Tests in Python, Part 2: Game of Life",
        "notes": "Worth continuing with as part of getting going with testing.",
        "link": "https://blog.miguelgrinberg.com/post/how-to-write-unit-tests-in-python-part-2-game-of-life"
    }
"""
