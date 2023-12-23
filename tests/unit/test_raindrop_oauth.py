from unittest import mock
from unittest.mock import patch
import pytest
import tempfile
import os

from raindrop import RaindropOauthHandler


@pytest.fixture
def raindrop_oauth():
    """
    Used by the following series of test classes which test the RoamApiInterface
    """
    return RaindropOauthHandler()


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
            raindrop = RaindropOauthHandler()
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
    
    def test_new_token_create_body_valid(self, raindrop_oauth):
        authorization_code = "1234"
        expected_body = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "client_id": raindrop_oauth.RAINDROP_CLIENT_ID,
                "client_secret": raindrop_oauth.RAINDROP_CLIENT_SECRET,
                "redirect_uri": "http://localhost",
        }
        body = raindrop_oauth._new_token_create_body(authorization_code)
        assert body == expected_body
        
        
    def test_refresh_token_create_body_valid(self, raindrop_oauth):
        expected_body =  {
            "client_id": raindrop_oauth.RAINDROP_CLIENT_ID,
            "client_secret": raindrop_oauth.RAINDROP_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": raindrop_oauth.RAINDROP_REFRESH_TOKEN
        }
        body = raindrop_oauth._refresh_token_create_body()
        assert body == expected_body
        
@pytest.fixture
def response_object_200():
    mock_response = mock.Mock()
    mock_response.status_code = 200
    mock_response.text = "Success"
    mock_response.json.return_value = {"access_token": "I am your access token"}    
    return mock_response
        
class TestValidateApiResponse:
    
    def test_check_200_response_success(self, raindrop_oauth, response_object_200):
        assert raindrop_oauth._response_validator(response_object_200) == None
    
    def test_check_200_response_failure(self, raindrop_oauth):
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        with pytest.raises(ValueError, match="Response status code is not 200"):
            raindrop_oauth._response_validator(mock_response)
                
    def test_check_200_but_token_missing(self, raindrop_oauth, response_object_200):
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        with pytest.raises(ValueError, match="Response code 200 but no token in response."):
            raindrop_oauth._response_validator(mock_response)
                
    def test_extract_oauth_token(self, raindrop_oauth, response_object_200):
        assert raindrop_oauth._extract_oauth_token(response_object_200) == "I am your access token"

    # def test_check_200_response_success(self, raindrop_oauth):
    #     mock_response = mock.Mock()
    #     mock_response.status_code = 200
    #     assert raindrop_oauth._check_200_response(mock_response) == True
    
    # def test_check_200_response_failure(self, raindrop_oauth):
    #     mock_response = mock.Mock()
    #     mock_response.status_code = 400
    #     mock_response.text = "Bad Request"
    #     assert raindrop_oauth._check_200_response(mock_response) == False
        
    # def test_extract_oauth_token(self, raindrop_oauth):
    #     mock_response = mock.Mock()
    #     mock_response.json.return_value = {"access_token": "I am your access token"}
    #     assert raindrop_oauth._extract_oauth_token(mock_response) == "I am your access token"

@pytest.fixture
def write_to_blank_env(raindrop_oauth):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write("Existing content\n")
            temp_file = temp.name
        raindrop_oauth.env_file = temp_file
        raindrop_oauth._write_token_to_env("test_token")
        with open(temp_file, "r") as f:
            lines = f.readlines()
        os.remove(temp_file)
        return lines            
        
@pytest.fixture
def write_to_complete_env(raindrop_oauth):
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write("".join
                       (
                           [
                "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
                "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
                "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
                "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
                "RAINDROP_OAUTH_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
                    ]
                )                
            )
            temp_file = temp.name
        raindrop_oauth.env_file = temp_file
        raindrop_oauth._write_token_to_env("test_token")
        with open(temp_file, "r") as f:
            lines = f.readlines()
        os.remove(temp_file)
        return lines 
        
class TestWriteToEnv:
    """
    TODO:  In progress rewriting these tests before starting to rewrite 
    RaindropOauthHandler._write_token_to_env per issue #3.
    """
    def test_check_token_no_prev_oauth(self, raindrop_oauth, write_to_blank_env):
        """
        TODO: This currently passes with the defective code - as the defect is that
        the previous tokens are never removed. Here - there are no previous tokens.
        """
        for line in write_to_blank_env: 
            if line.startswith("RAINDROP_OAUTH_TOKEN"):
                expected = line
                break
        assert  expected == "RAINDROP_OAUTH_TOKEN='test_token'\n"
        
    def test_number_of_tokens_no_prev_oauth(self, raindrop_oauth, write_to_blank_env):
        expected_lines = 0
        for line in write_to_blank_env:
            if line.startswith("RAINDROP_OAUTH_TOKEN"):
                expected_lines += 1
        assert expected_lines == 1
        
    def test_check_token_full_env(self, raindrop_oauth, write_to_complete_env):
        """
        TODO: Fails here as it finds the FIRST result - whereas the defective code adds
        """
        for line in write_to_complete_env: 
            if line.startswith("RAINDROP_OAUTH_TOKEN"):
                expected = line
                break
        assert  expected == "RAINDROP_OAUTH_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
        
    def test_number_of_tokens_full_env(self, raindrop_oauth, write_to_complete_env):
        expected_lines = 0
        for line in write_to_complete_env:
            if line.startswith("RAINDROP_OAUTH_TOKEN"):
                expected_lines += 1
        assert expected_lines == 1