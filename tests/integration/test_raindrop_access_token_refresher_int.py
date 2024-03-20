from unittest.mock import patch, mock_open


def custom_open_mock(*args, **kwargs):
    """
    Checks if a call to open is uses the 'w' method. Returns a mock if so, or else
    returns the original open call.
    """
    if args[1] == "w":
        return mock_open()(*args, **kwargs)
    else:
        return open(*args, **kwargs)


class TestAccessTokenRefreshRunner:
    # Patch the environment variable.
    @patch("os.environ", {"RAINDROP_REFRESH_TOKEN": "mock_refresh_token"})
    @patch("raindrop.open", side_effect=custom_open_mock)
    # Prevents creation of .env.backup in evfm._write_new_body_to_env
    @patch("shutil.copy")
    # Patches rcm.make_request to return response_object_200, which contains a 200
    # status code and a json.return value of {"access_token": "I am your access token"}
    @patch("raindrop.RaindropCredentialsManager.make_request")
    def test_happy_path(
        self,
        mock_make_request,
        mock_copy,
        mock_open,
        raindrop_access_token_refresher,
        response_object_200,
    ):
        """Tests refresh_token_process_runner as an integration test.

        See `RaindropAccessTokenRefresher.refresh_token_process_runner` for a step-by-
        step description.

        Patches shutil globally to avoid creating the backup .env copy in
        _write_new_body_to_env.

        Patches open in when called in the raindrop.py module, calling the side effect
        "custom_open_mock" which checks if it's a 'w' open.  This allows the other
        methods to open and read from the real .env file, whilst disallowing the
        overwrite in _write_new_body_to_env.
        """
        mock_make_request.return_value = response_object_200
        expected = None
        actual = raindrop_access_token_refresher.refresh_token_process_runner()
        assert actual == expected
