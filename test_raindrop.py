from unittest import mock
from unittest.mock import patch
import pytest
import tempfile
import os

from raindrop import RaindropGetNewOauth


@pytest.fixture
def raindrop_oauth():
    """
    Used by the following series of test classes which test the RoamApiInterface
    """
    return RaindropGetNewOauth()


class TestOauthInit:
           
    def test_rd_client_id_not_none(self, raindrop_oauth):
        assert raindrop_oauth.RAINDROP_CLIENT_ID != None
        
    def test_client_id_familiar_length(self, raindrop_oauth):
        """
        Client id may not always be 24 char
        """
        assert len(raindrop_oauth.RAINDROP_CLIENT_ID) == 24

    def test_client_id_alpha_numeric(self, raindrop_oauth):
        """
        Client ID may not always be alnum
        """
        assert raindrop_oauth.RAINDROP_CLIENT_ID.isalnum() == True
    
    def test_rd_client_secret_not_none(self, raindrop_oauth):
        assert raindrop_oauth.RAINDROP_CLIENT_SECRET != None

    def test_rd_client_secret_familiar_length(self, raindrop_oauth):
        assert len(raindrop_oauth.RAINDROP_CLIENT_SECRET) == 36

    def test_client_secret_uuid_format(self, raindrop_oauth):
        import re

        def is_uuid(value):
            uuid_regex = re.compile(
                r'^[0-9a-f]{8}-'
                r'[0-9a-f]{4}-'
                r'4[0-9a-f]{3}-'
                r'[89ab][0-9a-f]{3}-'
                r'[0-9a-f]{12}\Z', re.I)
            return bool(uuid_regex.match(value))

        assert is_uuid(raindrop_oauth.RAINDROP_CLIENT_SECRET) == True

    def test_redirect_uri_correct(self, raindrop_oauth):
        assert raindrop_oauth.REDIRECT_URI == "http://localhost"
    
    def test_base_url_correct(self, raindrop_oauth):
        assert raindrop_oauth.AUTH_CODE_BASE_URL == "https://raindrop.io/oauth/authorize"
        
    def test_headers_correct(self, raindrop_oauth):
        assert raindrop_oauth.HEADERS == {"Content-Type": "application/json"}

        
class TestOpenAuthCodeUrl:
        
    @patch('webbrowser.open')
    def test_open_authorization_code_url_creates_url_correctly(self, mock_webbrowser_open, raindrop_oauth):
        raindrop_oauth._open_authorization_code_url()
        expected_url = f"https://raindrop.io/oauth/authorize?client_id={raindrop_oauth.RAINDROP_CLIENT_ID}&redirect_uri={raindrop_oauth.REDIRECT_URI}"
        actual_url = mock_webbrowser_open.call_args[0][0]
        assert actual_url == expected_url    


class TestUserPasteValidAuthCodeUrl:
    
    def test_user_paste_valid_input(self, raindrop_oauth):
        with patch('builtins.input', return_value='http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7'):
            result = raindrop_oauth._user_paste_valid_auth_code_url()
        assert result == 'http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7'

    def test_user_paste_valid_auth_code_url_invalid_then_valid_input(self, raindrop_oauth):
        with patch('builtins.input', side_effect=['invalid_url', 'http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7']):
            raindrop = RaindropGetNewOauth()
            result = raindrop_oauth._user_paste_valid_auth_code_url()
            assert result == 'http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7'
 
class TestParseAuthorizationCodeUrl:
     
    def test_parse_auth_code_url_valid(self, raindrop_oauth):
        authorization_code = raindrop_oauth._parse_authorization_code_url('http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7')
        expected_authorization_code = 'aa4c0bc8-0e19-4615-a032-bd3379829ca7'
        assert authorization_code == expected_authorization_code
        
    def test_parse_auth_code_url_alternate_code_format_length(self, raindrop_oauth):
        authorization_code = raindrop_oauth._parse_authorization_code_url('http://localhost/?code=aa4c0bc8')
        expected_authorization_code = 'aa4c0bc8'
        assert authorization_code == expected_authorization_code
        
class TestCreateBody:
    
    def test_create_body_valid(self, raindrop_oauth):
        authorization_code = "1234"
        expected_body = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "client_id": raindrop_oauth.RAINDROP_CLIENT_ID,
                "client_secret": raindrop_oauth.RAINDROP_CLIENT_SECRET,
                "redirect_uri": "http://localhost",
        }
        body = raindrop_oauth._create_body(authorization_code)
        assert body == expected_body
        
class TestValidateApiResponse:
    
    def test_check_200_response_success(self, raindrop_oauth):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        assert raindrop_oauth._check_200_response(mock_response) == True
    
    def test_check_200_response_failure(self, raindrop_oauth):
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        assert raindrop_oauth._check_200_response(mock_response) == False
        
    def test_extract_oauth_token(self, raindrop_oauth):
        mock_response = mock.Mock()
        mock_response.json.return_value = {"access_token": "I am your access token"}
        assert raindrop_oauth._extract_oauth_token(mock_response) == "I am your access token"

class TestWriteToEnv:
    
    def test_write_token_to_env(self, raindrop_oauth):
        """

        """
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write("Existing content\n")
            temp_file = temp.name
        raindrop_oauth.env_file = temp_file
        raindrop_oauth._write_token_to_env("test_token")
        with open(temp_file, "r") as f:
            lines = f.readlines()
        assert lines[-1] == "RAINDROP_OAUTH_TOKEN='test_token'\n"
        os.remove(temp_file)

        