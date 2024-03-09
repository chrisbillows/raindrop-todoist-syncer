from unittest.mock import Mock, patch, mock_open
import pytest

from raindrop import RaindropOauthHandler

@pytest.fixture
def raindrop_oauth():
    return RaindropOauthHandler()

@pytest.fixture
def response_valid():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"access_token":"NEW OAUTH TOKEN"}
    return mock_response

def custom_open_mock(*args, **kwargs):
    """
    Checks if a call to open is uses the 'w' method. Returns a mock if so, or else 
    returns the original open call.
    """
    if args[1] == 'w':
        return mock_open()(*args, **kwargs)
    else:
        return open(*args, **kwargs)
    
class TestOauthRefreshTokenRunner:
    
    def test_valid_response(self, raindrop_oauth,response_valid):
        """
        Patches the request with the mock response object `response valid` - which is
        assigned a status code and a json.return_valye.
        
        Patches shutil globally to avoid creating the backup .env copy in
        _write_new_body_to_env.  
        
        Patches open in when called in the raindrop.py module, calling the side effect
        "custom_open_mock" which checks if it's a 'w' open.  This allows the other 
        methods to open and read from the real .env file, whilst disallowing the 
        overwrite in _write_new_body_to_env.
        """
        expected = True
        with patch('raindrop.RaindropOauthHandler._make_request', return_value=response_valid), \
             patch('shutil.copy'), \
             patch('raindrop.open', side_effect=custom_open_mock):
            actual = raindrop_oauth.refresh_token_process_runner() 
        assert actual == expected
        
        def test_more_test_cases(self):
            """
            TODO: Complete more test cases. Think integration rather than just repeats 
            of unit tests.
            """
            pass
