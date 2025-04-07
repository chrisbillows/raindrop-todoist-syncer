from unittest.mock import patch


def test_fixture_doesnt_use_real_env_files(
    raindrop_access_token_refresher_for_file_overwriting,
):
    # Test the `raindrop_access_token_refresher` is not using the users .env file or the
    # .env.test file - and therefore using a tmp_path file.
    expected = [".env", ".env.test"]
    evfm = raindrop_access_token_refresher_for_file_overwriting.evfm
    actual = evfm.env_file
    assert actual not in expected


def extract_access_token_from_env_file(env_file):
    # Takes a .env_file, reads it into memory and finds the RAINDROP_ACCESS_TOKEN
    # line then extracts the `access_token` from the line string.
    with open(env_file, "r") as file:
        lines = file.readlines()

    for idx, line in enumerate(lines):
        if line.startswith("RAINDROP_ACCESS_TOKEN"):
            target_line = line
            access_token = target_line.split("=")[1].strip().strip("'")
            return access_token


class TestAccessTokenRefreshRunner:
    # These tests use the `raindrop_access_token_refresher_for_file_overwriting` so
    # that the overwriting the new .env can also be tested.
    #
    # The only mocked element is the request to the Raindrop.io API itself.

    # Patches `rcm.make_request`` which requests a new Oauth2 access token.
    @patch(
        "raindrop_todoist_syncer.rd_credentials.RaindropCredentialsManager.make_request"
    )
    def test_happy_path(
        self,
        mock_make_request,
        oauth_request_response_object_200,
        raindrop_access_token_refresher_for_file_overwriting,
    ):
        ratr = raindrop_access_token_refresher_for_file_overwriting

        # Sets the return value mock request.
        mock_make_request.return_value = oauth_request_response_object_200

        expected = "I am your access token"
        actual = ratr.refresh_token_process_runner()

        assert actual == expected

    # Patches `rcm.make_request`` which requests a new Oauth2 access token.
    @patch(
        "raindrop_todoist_syncer.rd_credentials.RaindropCredentialsManager.make_request"
    )
    def test_temp_env_file_updated_correctly(
        self,
        mock_make_request,
        oauth_request_response_object_200,
        raindrop_access_token_refresher_for_file_overwriting,
    ):
        ratr = raindrop_access_token_refresher_for_file_overwriting

        # Sets the return value mock request.
        mock_make_request.return_value = oauth_request_response_object_200

        # Run the function.
        ratr.refresh_token_process_runner()

        # Extracted the now updated environment file.
        temp_env_file = ratr.evfm.env_file

        # Extract the newly written access token
        actual = extract_access_token_from_env_file(temp_env_file)
        expected = "I am your access token"
        assert actual == expected

    @patch(
        "raindrop_todoist_syncer.rd_credentials.RaindropCredentialsManager.make_request"
    )
    def test_temp_env_file_backedup_correctly(
        self,
        mock_make_request,
        oauth_request_response_object_200,
        raindrop_access_token_refresher_for_file_overwriting,
    ):
        ratr = raindrop_access_token_refresher_for_file_overwriting

        # Sets the return value mock request.
        mock_make_request.return_value = oauth_request_response_object_200

        expected = None

        # Run the function.
        ratr.refresh_token_process_runner()
        # Extracted the now updated environment file.
        temp_backup = ratr.evfm.env_backup

        actual = extract_access_token_from_env_file(temp_backup)
        expected = "klmno"

        assert actual == expected
