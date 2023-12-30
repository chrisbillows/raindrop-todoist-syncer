from unittest import mock
from unittest.mock import patch, mock_open
import pytest
import tempfile
import os

from raindrop import DuplicateOauthTokenError, EnvDataOverwriteError, OauthTokenNotWrittenError, RaindropOauthHandler


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

class TestMakeRequest:
    """
    Only unit testable part would be construction of post request body - and it's so
    simple as to be meaningless.
    """
    pass

        
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

class TestExtractOauthToken:
    
    def test_extract_oauth_token(self, raindrop_oauth, response_object_200):
        assert raindrop_oauth._extract_oauth_token(response_object_200) == "I am your access token"

    
@pytest.fixture
def placeholder_one_liner_env():
    mock_content = "Existing content\n"
    return mock_content

@pytest.fixture
def full_env_oauth_first():
    mock_content = [
            "RAINDROP_OAUTH_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
                ]
    return "".join(mock_content)

@pytest.fixture
def full_env_oauth_middle():
    mock_content = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_OAUTH_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
                ]
    return "".join(mock_content)

@pytest.fixture
def full_env_oauth_last():
    mock_content = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_OAUTH_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
                ]
    return "".join(mock_content)

class TestCreateUpdatedEnvBody:
        
    @pytest.mark.parametrize(
        "mock_env",
        [
         "placeholder_one_liner_env",
         "full_env_oauth_first",
         "full_env_oauth_middle",
         "full_env_oauth_last"
        ]
    )
    def test_only_one_raindrop_oauth_token_present(self, raindrop_oauth, request, mock_env):
        """Test only one raindrop oauth token present in newly created .env body."""
        mock_env_content = request.getfixturevalue(mock_env)
        
        mocked_open = mock_open(read_data=mock_env_content) 
        with patch('builtins.open', mocked_open):
            updated_lines = raindrop_oauth._create_updated_env_body("test_token")
        expected_lines = []
        for line in updated_lines:
            if line.startswith("RAINDROP_OAUTH"):
                expected_lines.append(line)
        assert len(expected_lines) == 1
        
    @pytest.mark.parametrize(
        "mock_env, expected_lines",
        [
         ("placeholder_one_liner_env", 2),
         ("full_env_oauth_first", 5),
         ("full_env_oauth_middle", 5),
         ("full_env_oauth_last", 5)
        ]
    )
    def test_num_of_lines_correct(self, raindrop_oauth, request, mock_env, expected_lines):
        """Test number of lines in new .env body is expected
    
        If the previous .env had no oauth token, the number of lines would increase by one.
    
        If the previous. env did have an oauth token, that line should be overwritten so 
        the number of lines should remain the same.
        """  
        mock_env_content = request.getfixturevalue(mock_env)
        mocked_open = mock_open(read_data=mock_env_content) 
        with patch('builtins.open', mocked_open):
            updated_lines = raindrop_oauth._create_updated_env_body("test_token")
        assert len(updated_lines) == expected_lines

class TestNewEnvValidator:
    
    def test_valid_simple_list(self, raindrop_oauth, request, placeholder_one_liner_env):
        """
        - Uses a fixture to supply the "old" env file via patch/mocked open. 
        - The mock new body is the output from _create_updated_env_body.
        - Result is the method call patched with the "old" env.
        - Expected is the new body returned untouched as `_new_env_validator` throws an
        error if it finds something it doesn't like.
        
        """
        mocked_open = mock_open(read_data=placeholder_one_liner_env) 
        
        mock_new_body = [
            "Existing Content\n",
            "RAINDROP_OAUTH_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
        ]
        
        with patch('builtins.open', mocked_open):
            result = raindrop_oauth._new_env_validator(mock_new_body)
        
        expected = mock_new_body
        
        assert result == expected
    
    def test_valid_full_list(self, raindrop_oauth, full_env_oauth_last):
        mocked_open = mock_open(read_data=full_env_oauth_last) 
                
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_OAUTH_TOKEN='A fresh new token'\n"
        ]
        
        with patch('builtins.open', mocked_open):
            result = raindrop_oauth._new_env_validator(mock_new_body)
        
        expected = mock_new_body
        
        assert result == expected 
            
    def test_invalid_duplicate_token_middle_last(self, raindrop_oauth, full_env_oauth_middle):
        mocked_open = mock_open(read_data=full_env_oauth_middle) 
                
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_OAUTH_TOKEN ='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_OAUTH_TOKEN = 'New token added instead of overwritten'\n"
        ]
        with pytest.raises(DuplicateOauthTokenError):
            with patch('builtins.open', mocked_open):    
                raindrop_oauth._new_env_validator(mock_new_body)

    def test_invalid_duplicate_token_both_at_end(self, raindrop_oauth, full_env_oauth_last):
        mocked_open = mock_open(read_data=full_env_oauth_last) 
                
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_OAUTH_TOKEN ='8bde7733-b4de-4fb5-92ab-2709434a504e'\n",
            "RAINDROP_OAUTH_TOKEN = 'New token added instead of overwritten'\n"
        ]
        with pytest.raises(DuplicateOauthTokenError):
            with patch('builtins.open', mocked_open):    
                raindrop_oauth._new_env_validator(mock_new_body)
   
    def test_blank_line_added(self, raindrop_oauth, full_env_oauth_last):
        mocked_open = mock_open(read_data=full_env_oauth_last) 
                
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "\n",
            "rogue data\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_OAUTH_TOKEN = 'New token'\n"
        ]
        with pytest.raises(EnvDataOverwriteError):
            with patch('builtins.open', mocked_open):    
                raindrop_oauth._new_env_validator(mock_new_body)
      
    #! THIS ERROR IS NOT CURRENTLY PICKED UP. RAISED ISSUE #6.       
    # def test_non_oauth_token_deleted(self, raindrop_oauth, full_env_oauth_last):
    #     mocked_open = mock_open(read_data=full_env_oauth_last) 
                
    #     mock_new_body = [
    #         "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
    #         "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
    #         "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
    #         "RAINDROP_OAUTH_TOKEN = 'New token instead of overwritten'\n"
    #     ]
    #     with pytest.raises(EnvDataOverwriteError):
    #         with patch('builtins.open', mocked_open):    
    #             raindrop_oauth._new_env_validator(mock_new_body)
                
    def test_env_unchanged(self, raindrop_oauth, full_env_oauth_last):
        mocked_open = mock_open(read_data=full_env_oauth_last) 
                
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_OAUTH_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
        ]
        with pytest.raises(EnvDataOverwriteError):
            with patch('builtins.open', mocked_open):    
                raindrop_oauth._new_env_validator(mock_new_body)

    def test_no_token_written(self, raindrop_oauth, placeholder_one_liner_env):
        mocked_open = mock_open(read_data=placeholder_one_liner_env) 
        mock_new_body = [
            "Existing Content\n",
            "A random new line of content!\n"
        ]
        with pytest.raises(OauthTokenNotWrittenError):
            with patch('builtins.open', mocked_open):    
                raindrop_oauth._new_env_validator(mock_new_body)


class TestWriteNewBodyToEnv:
    
    def test_successful_write(self, raindrop_oauth):
        valid_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_OAUTH_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
        ]
        mocked_open = mock_open()
        
        with patch('shutil.copy') as mock_copy, patch('builtins.open', mocked_open):
            result = raindrop_oauth._write_new_body_to_env(valid_body)
            mock_copy.assert_called_once_with('.env', '.env.backup')
            
            mocked_open.assert_called_once_with('.env', 'w')
            mocked_open.return_value.writelines.assert_called_once_with(valid_body)
            
            assert result is True    
