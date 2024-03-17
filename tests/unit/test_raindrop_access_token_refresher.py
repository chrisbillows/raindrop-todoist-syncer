import pytest

from raindrop import (
    RaindropAccessTokenRefresher,
    RaindropCredentialsManager,
    EnvironmentVariablesFileManager,
)


@pytest.fixture
def raindrop_access_token_refresher():
    evfm = EnvironmentVariablesFileManager
    rcm = RaindropCredentialsManager()
    return RaindropAccessTokenRefresher(rcm, evfm)


class TestCreateBody:
    def test_refresh_token_create_body_valid(self, raindrop_access_token_refresher):
        expected_body = {
            "client_id": raindrop_access_token_refresher.rcm.RAINDROP_CLIENT_ID,
            "client_secret": raindrop_access_token_refresher.rcm.RAINDROP_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": raindrop_access_token_refresher.rcm.RAINDROP_REFRESH_TOKEN,
        }
        body = raindrop_access_token_refresher._refresh_token_create_body()
        assert body == expected_body
