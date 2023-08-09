from unittest import mock
import pytest

from raindrop import Raindrop


@pytest.fixture
def raindrop_class():
   return Raindrop()

@pytest.fixture
def raindrop_body():
    rd = mock.Mock()
    rd.id = ""
    rd.created_time = ""
    rd.parsed_time = ""
    rd.title = ""
    rd.notes = ""
    rd.link = ""
    return rd
    
@pytest.fixture
def rd_raw_api_response():
    requests_obj = mock.Mock()
    requests_obj.status_code = "200"
    # ...
    return requests_obj
    
# RAW RAINDROP EXAMPLE
"""
{'_id': 621872658,
 'broken': False,
 'cache': {'created': '2023-08-06T19:57:10.000Z',
           'size': 182846,
           'status': 'ready'},
 'collection': {'$id': 31352328, '$ref': 'collections', 'oid': 31352328},
 'collectionId': 31352328,
 'cover': 'https://opengraph.githubassets.com/e1bbb2f1946ae6b1b3182a2a7e226114ffff058910f8426d1aad736dff6b513d/tadashi-aikawa/shukuchi',
 'created': '2023-08-06T19:56:44.948Z',
 'creatorRef': {'_id': 645158,
                'avatar': '',
                'email': '',
                'name': 'christopherbillows'},
 'domain': 'github.com',
 'excerpt': 'Shukuchi is an Obsidian plugin that enables you to teleport to '
            'links (URL or internal link). - tadashi-aikawa/shukuchi: Shukuchi '
            'is an Obsidian plugin that enables you to teleport to links (URL '
            'or ...',
 'highlights': [],
 'important': False,
 'lastUpdate': '2023-08-06T19:56:46.806Z',
 'link': 'https://github.com/tadashi-aikawa/shukuchi',
 'media': [{'link': 'https://opengraph.githubassets.com/e1bbb2f1946ae6b1b3182a2a7e226114ffff058910f8426d1aad736dff6b513d/tadashi-aikawa/shukuchi',
            'type': 'image'},
           {'link': 'https://raw.githubusercontent.com/tadashi-aikawa/shukuchi/master/resources/direction-of-possible-teleportation.png',
            'type': 'image'}],
 'note': '',
 'reminder': {'date': None},
 'removed': False,
 'sort': 621872658,
 'tags': [],
 'title': 'tadashi-aikawa/shukuchi: Shukuchi is an Obsidian plugin that '
          'enables you to teleport to links (URL or internal link).',
 'type': 'link',
 'user': {'$id': 645158, '$ref': 'users'}}
""" 

"""
OUR JSON EXAMPLE
    {
        "id": 588482518,
        "created_time": "2023-06-09T14:45:58.831Z",
        "parsed_time": "2023-06-14T16:10:14.085+00:00",
        "title": "How to Write Unit Tests in Python, Part 2: Game of Life",
        "notes": "Worth continuing with as part of getting going with testing.",
        "link": "https://blog.miguelgrinberg.com/post/how-to-write-unit-tests-in-python-part-2-game-of-life"
    }
"""


class TestInit:
    """
    Early warning system for my own idiocy.    
    """    
    
    def test_init_id():
        pass
    
    