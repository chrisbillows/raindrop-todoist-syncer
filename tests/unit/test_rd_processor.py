from unittest import mock
from unittest.mock import patch

import pytest

from raindrop import RaindropsProcessor

@pytest.fixture
def raindrop_oauth():
    """
    Used by the following series of test classes which test the RoamApiInterface
    """
    return RaindropsProcessor()

class TestProcessorInit:
    
    def test_basic_init(self):
        pass