import pytest

from raindrop_todoist_syncer.rd_credentials import RaindropCredentialsManager


@pytest.fixture
def raindrop_credentials_manager(mock_user_config):
    return RaindropCredentialsManager(mock_user_config)


class TestRaindropCredentialsManagerInit:
    def test_auth_base_url_correct(self, raindrop_credentials_manager):
        expected = "https://raindrop.io/oauth/authorize"
        actual = raindrop_credentials_manager.AUTH_CODE_BASE_URL
        assert actual == expected

    def test_redirect_uri_correct(self, raindrop_credentials_manager):
        expected = "http://localhost"
        actual = raindrop_credentials_manager.REDIRECT_URI
        assert actual == expected

    def test_headers_correct(self, raindrop_credentials_manager):
        expected = {"Content-Type": "application/json"}
        actual = raindrop_credentials_manager.HEADERS
        assert actual == expected

    def test_env_vars_output_correctly(self, mock_user_config):
        rcm = RaindropCredentialsManager(mock_user_config)
        assert rcm.RAINDROP_CLIENT_ID == "cd34"
        assert rcm.RAINDROP_CLIENT_SECRET == "ef56"
        assert rcm.RAINDROP_REFRESH_TOKEN == "gh78"
        assert rcm.RAINDROP_ACCESS_TOKEN == "ij910"


class TestRaindropCredentialsManagerMakeRequest:
    """
    Only unit testable part would be construction of post request body - and it's so
    simple as to be meaningless.
    """

    pass


class TestRaindropCredentialsManagerResponseValidator:
    def test_check_200_response_success(
        self, raindrop_credentials_manager, oauth_request_response_object_200
    ):
        expected = None
        actual = raindrop_credentials_manager.response_validator(
            oauth_request_response_object_200
        )
        assert actual == expected

    def test_check_200_response_failure(
        self, raindrop_credentials_manager, oauth_request_response_object_400
    ):
        with pytest.raises(ValueError, match="Response status code is not 200"):
            raindrop_credentials_manager.response_validator(
                oauth_request_response_object_400
            )

    def test_check_200_but_token_missing(
        self,
        raindrop_credentials_manager,
        oauth_request_response_object_200_but_no_token,
    ):
        with pytest.raises(
            ValueError, match="Response code 200 but no token in response."
        ):
            raindrop_credentials_manager.response_validator(
                oauth_request_response_object_200_but_no_token
            )


class TestExtractAccessToken:
    def test_extract_oauth_token(
        self, raindrop_credentials_manager, oauth_request_response_object_200
    ):
        assert (
            raindrop_credentials_manager.extract_access_token(
                oauth_request_response_object_200
            )
            == "I am your access token"
        )
