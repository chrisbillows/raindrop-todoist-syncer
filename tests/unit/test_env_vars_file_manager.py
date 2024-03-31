from unittest.mock import patch, mock_open

import pytest

from raindrop_todoist_syncer.raindrop import (
    DuplicateAccessTokenError,
    EnvDataOverwriteError,
    AccessTokenNotWrittenError,
)


class TestCreateEnvBodyWithUpdatedAccessToken:
    @pytest.mark.parametrize(
        "mock_env",
        [
            "placeholder_one_liner_env",
            "full_env_oauth_first",
            "full_env_oauth_middle",
            "full_env_oauth_last",
        ],
    )
    def test_only_one_raindrop_oauth_token_present(
        self, environmental_variables_file_manager, request, mock_env
    ):
        """Test only one raindrop oauth token present in newly created .env body."""
        mock_env_content = request.getfixturevalue(mock_env)
        mocked_open = mock_open(read_data=mock_env_content)
        with patch("builtins.open", mocked_open):
            updated_lines = environmental_variables_file_manager._create_env_body_with_updated_access_token(
                "test_token"
            )
        expected_lines = []
        for line in updated_lines:
            if line.startswith("RAINDROP_ACCESS"):
                expected_lines.append(line)
        assert len(expected_lines) == 1

    @pytest.mark.parametrize(
        "mock_env, expected_lines",
        [
            ("placeholder_one_liner_env", 2),
            ("full_env_oauth_first", 5),
            ("full_env_oauth_middle", 5),
            ("full_env_oauth_last", 5),
        ],
    )
    def test_num_of_lines_correct(
        self, environmental_variables_file_manager, request, mock_env, expected_lines
    ):
        """Test number of lines in new .env body is expected

        If the previous .env had no oauth token, the number of lines would increase by one.

        If the previous .env did have an oauth token, that line should be overwritten so
        the number of lines should remain the same.
        """
        mock_env_content = request.getfixturevalue(mock_env)
        mocked_open = mock_open(read_data=mock_env_content)
        with patch("builtins.open", mocked_open):
            updated_lines = environmental_variables_file_manager._create_env_body_with_updated_access_token(
                "test_token"
            )
        assert len(updated_lines) == expected_lines


class TestNewEnvValidator:
    def test_valid_simple_list(
        self, environmental_variables_file_manager, request, placeholder_one_liner_env
    ):
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
            "RAINDROP_ACCESS_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n",
        ]
        with patch("builtins.open", mocked_open):
            result = environmental_variables_file_manager._new_env_validator(
                mock_new_body
            )
        expected = mock_new_body
        assert result == expected

    def test_valid_full_list(
        self, environmental_variables_file_manager, full_env_oauth_last
    ):
        mocked_open = mock_open(read_data=full_env_oauth_last)
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_ACCESS_TOKEN='A fresh new token'\n",
        ]
        with patch("builtins.open", mocked_open):
            result = environmental_variables_file_manager._new_env_validator(
                mock_new_body
            )
        expected = mock_new_body
        assert result == expected

    def test_invalid_duplicate_token_middle_last(
        self, environmental_variables_file_manager, full_env_oauth_middle
    ):
        mocked_open = mock_open(read_data=full_env_oauth_middle)

        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_ACCESS_TOKEN ='8bde7733-b4de-4fb5-92ab-2709434a504e'\n"
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_ACCESS_TOKEN = 'New token added instead of overwritten'\n",
        ]
        with pytest.raises(DuplicateAccessTokenError):
            with patch("builtins.open", mocked_open):
                environmental_variables_file_manager._new_env_validator(mock_new_body)

    def test_invalid_duplicate_token_both_at_end(
        self, environmental_variables_file_manager, full_env_oauth_last
    ):
        mocked_open = mock_open(read_data=full_env_oauth_last)

        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_ACCESS_TOKEN ='8bde7733-b4de-4fb5-92ab-2709434a504e'\n",
            "RAINDROP_ACCESS_TOKEN = 'New token added instead of overwritten'\n",
        ]
        with pytest.raises(DuplicateAccessTokenError):
            with patch("builtins.open", mocked_open):
                environmental_variables_file_manager._new_env_validator(mock_new_body)

    def test_blank_line_added(
        self, environmental_variables_file_manager, full_env_oauth_last
    ):
        mocked_open = mock_open(read_data=full_env_oauth_last)
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "\n",
            "rogue data\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_ACCESS_TOKEN = 'New token'\n",
        ]
        with pytest.raises(EnvDataOverwriteError):
            with patch("builtins.open", mocked_open):
                environmental_variables_file_manager._new_env_validator(mock_new_body)

    @pytest.mark.skip(reason="THIS ERROR IS NOT CURRENTLY PICKED UP. RAISED ISSUE #6")
    def test_non_oauth_token_deleted(
        self, environmental_variables_file_manager, full_env_oauth_last
    ):
        mocked_open = mock_open(read_data=full_env_oauth_last)
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_ACCESS_TOKEN = 'New token instead of overwritten'\n",
        ]
        with pytest.raises(EnvDataOverwriteError):
            with patch("builtins.open", mocked_open):
                environmental_variables_file_manager._new_env_validator(mock_new_body)

    def test_env_unchanged(
        self, environmental_variables_file_manager, full_env_oauth_last
    ):
        mocked_open = mock_open(read_data=full_env_oauth_last)
        mock_new_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_ACCESS_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n",
        ]
        with pytest.raises(EnvDataOverwriteError):
            with patch("builtins.open", mocked_open):
                environmental_variables_file_manager._new_env_validator(mock_new_body)

    def test_no_token_written(
        self, environmental_variables_file_manager, placeholder_one_liner_env
    ):
        mocked_open = mock_open(read_data=placeholder_one_liner_env)
        mock_new_body = ["Existing Content\n", "A random new line of content!\n"]
        with pytest.raises(AccessTokenNotWrittenError):
            with patch("builtins.open", mocked_open):
                environmental_variables_file_manager._new_env_validator(mock_new_body)


class TestWriteNewBodyToEnv:
    def test_successful_write(self, environmental_variables_file_manager):
        valid_body = [
            "TODOIST_API_KEY = 'c691d501580e381be70d1a97f5k6624d5939b142'\n",
            "RAINDROP_CLIENT_ID = '6491cb52xvt44917d70b2d7a'\n",
            "RAINDROP_CLIENT_SECRET = '22914d01-5c7b-49a5-c928-a229ed013c66'\n",
            "RAINDROP_REFRESH_TOKEN = 'b8791s45-e83f-4699-al48-39693177h296'\n",
            "RAINDROP_ACCESS_TOKEN='8bde7733-b4de-4fb5-92ab-2709434a504e'\n",
        ]
        mocked_open = mock_open()
        with patch("shutil.copy") as mock_copy, patch("builtins.open", mocked_open):
            result = environmental_variables_file_manager._write_new_body_to_env(
                valid_body
            )
            mock_copy.assert_called_once_with(".env", ".env.backup")
            mocked_open.assert_called_once_with(".env", "w")
            mocked_open.return_value.writelines.assert_called_once_with(valid_body)
            assert result is None
