from unittest.mock import patch

import pytest

from raindrop_todoist_syncer.env_manage import EnvironmentVariablesFileManager
from raindrop_todoist_syncer.rd_credentials import RaindropCredentialsManager
from raindrop_todoist_syncer.rd_token import RaindropNewAccessTokenGetter


@pytest.fixture
def raindrop_new_access_token_getter(mock_user_config):
    evfm = EnvironmentVariablesFileManager(mock_user_config)
    rcm = RaindropCredentialsManager()
    return RaindropNewAccessTokenGetter(rcm, evfm)


class TestOpenAuthCodeUrl:
    @patch("webbrowser.open")
    def test_open_authorization_code_url_creates_url_correctly(
        self, mock_webbrowser_open, raindrop_new_access_token_getter
    ):
        raindrop_new_access_token_getter._open_authorization_code_url()
        expected_url = (
            f"https://raindrop.io/oauth/authorize?"
            f"client_id={raindrop_new_access_token_getter.rcm.RAINDROP_CLIENT_ID}&"
            f"redirect_uri={raindrop_new_access_token_getter.rcm.REDIRECT_URI}"
        )
        actual_url = mock_webbrowser_open.call_args[0][0]
        assert actual_url == expected_url


class TestUserPasteValidAuthCodeUrl:
    def test_user_paste_valid_input(self, raindrop_new_access_token_getter):
        with patch(
            "builtins.input",
            return_value="http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7",
        ):
            result = raindrop_new_access_token_getter._user_paste_valid_auth_code_url()
        assert result == "http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7"

    def test_user_paste_valid_auth_code_url_invalid_then_valid_input(
        self, raindrop_new_access_token_getter
    ):
        with patch(
            "builtins.input",
            side_effect=[
                "invalid_url",
                "http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7",
            ],
        ):
            result = raindrop_new_access_token_getter._user_paste_valid_auth_code_url()
            assert (
                result == "http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7"
            )


class TestParseAuthorizationCodeUrl:
    def test_parse_auth_code_url_valid(self, raindrop_new_access_token_getter):
        authorization_code = (
            raindrop_new_access_token_getter._parse_authorization_code_url(
                "http://localhost/?code=aa4c0bc8-0e19-4615-a032-bd3379829ca7"
            )
        )
        expected_authorization_code = "aa4c0bc8-0e19-4615-a032-bd3379829ca7"
        assert authorization_code == expected_authorization_code

    def test_parse_auth_code_url_alternate_code_format_length(
        self, raindrop_new_access_token_getter
    ):
        authorization_code = (
            raindrop_new_access_token_getter._parse_authorization_code_url(
                "http://localhost/?code=aa4c0bc8"
            )
        )
        expected_authorization_code = "aa4c0bc8"
        assert authorization_code == expected_authorization_code


class TestCreateBody:
    def test_new_token_create_body_valid(self, raindrop_new_access_token_getter):
        authorization_code = "1234"
        expected_body = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "client_id": raindrop_new_access_token_getter.rcm.RAINDROP_CLIENT_ID,
            "client_secret": raindrop_new_access_token_getter.rcm.RAINDROP_CLIENT_SECRET,
            "redirect_uri": "http://localhost",
        }
        body = raindrop_new_access_token_getter._new_token_create_body(
            authorization_code
        )
        assert body == expected_body
