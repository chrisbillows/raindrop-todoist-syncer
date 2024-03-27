from unittest.mock import patch


class TestAccessTokenRefreshRunner:
    # Patches the method that a) copies the .env file to .env.backup and b) overwrites
    # the .env file.
    @patch(
        "raindrop.EnvironmentVariablesFileManager._write_new_body_to_env",
        return_value=None,
    )
    # Patches rcm.make_request to return response_object_200, which contains a 200
    # status code and a json.return value of {"access_token": "I am your access token"}
    @patch("raindrop.RaindropCredentialsManager.make_request")
    def test_happy_path(
        self,
        mock_make_request,
        mock_write_new_body_to_env,
        raindrop_access_token_refresher,
        oauth_request_response_object_200,
    ):
        # Mocks a successful response for a new oauth access token
        mock_make_request.return_value = oauth_request_response_object_200
        expected = None
        actual = raindrop_access_token_refresher.refresh_token_process_runner()
        assert actual == expected
