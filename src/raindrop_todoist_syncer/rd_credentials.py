import json
import os

from dotenv import load_dotenv
from loguru import logger
import requests
from requests import Request, Response

load_dotenv()


class RaindropCredentialsManager:
    def __init__(self) -> None:
        """Provide variables and methods for managing Raindrop Oauth2 credentials."""
        self.env_file = ".env"
        self.AUTH_CODE_BASE_URL = "https://raindrop.io/oauth/authorize"
        self.REDIRECT_URI = "http://localhost"
        self.HEADERS = {"Content-Type": "application/json"}
        self.RAINDROP_CLIENT_ID = os.getenv("RAINDROP_CLIENT_ID")
        self.RAINDROP_CLIENT_SECRET = os.getenv("RAINDROP_CLIENT_SECRET")
        self.RAINDROP_REFRESH_TOKEN = os.getenv("RAINDROP_REFRESH_TOKEN")
        self.RAINDROP_ACCESS_TOKEN = os.getenv("RAINDROP_ACCESS_TOKEN")

    def make_request(self, body: dict[str, str]) -> Request:
        """Makes the an request and returns a Request object."""
        headers = self.HEADERS
        data = body
        oauth_response = requests.post(
            "https://raindrop.io/oauth/access_token",
            headers=headers,
            data=json.dumps(data),
        )
        return oauth_response

    def response_validator(self, response: Response) -> None:
        """Checks a Response object returned by the Raindrop API Oauth2 process is
        valid.
        """
        if response.status_code != 200:
            raise ValueError(
                "Response status code is not 200 (as required in the docs)."
                f"Status code was {response.status_code} - {response.text}"
            )

        if response.json().get("access_token") is None:
            raise ValueError(
                f"Response code 200 but no token in response. Full response {response.json()}"
            )

    def extract_access_token(self, oauth_response: Response) -> str:
        """Extracts the access token from the response.json of a Response object."""
        data = oauth_response.json()
        access_token = data.get("access_token")
        logger.info(
            f"Your access token is {access_token}. I am of type {type(access_token)}"
        )
        return access_token
