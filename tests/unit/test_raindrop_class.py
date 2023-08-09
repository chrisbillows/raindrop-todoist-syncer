from unittest import mock
import json
import pytest

from raindrop import Raindrop


# @pytest.fixture
# def raindrop_body():
#     rd = mock.Mock()
#     rd.id = ""
#     rd.created_time = ""
#     rd.parsed_time = ""
#     rd.title = ""
#     rd.notes = ""
#     rd.link = ""
#     return rd
    
@pytest.fixture
def rd_raw_api_response():
    requests_obj = mock.Mock()
    requests_obj.status_code = 200
    requests_obj.text = "This is some status code text."
    with open('tests/unit/rd_api_full_dot_json_.json', "r") as f:
        content = json.load(f)
        requests_obj.json = mock.Mock(return_value=content)
    return requests_obj
   

@pytest.fixture
def rd_extracted_single_raindrop_dict():
    """
    Returns a dictionary representation of a single raindrop. 
    In actual usage, this structure is typically extracted from a list of 
    raindrops that have been processed with json.load. For testing purposes, 
    this fixture loads the content of a single raindrop saved as JSON from a file.
    """
    with open('tests/unit/rd_api_single_rd.json', "r") as f:
        content = json.load(f)
    return content

@pytest.fixture
def raindrop_object(rd_extracted_single_raindrop_dict):
   return Raindrop(rd_extracted_single_raindrop_dict)

class TestInit:
    """
    Early warning system for my own idiocy.    
    """    
    def test_init_id(self, raindrop_object):
        assert raindrop_object.id == 621872658
   

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

    