from loguru import logger
from typing import Any, Dict, List

import requests
from requests import Response
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from raindrop_todoist_syncer.config import UserConfig
from raindrop_todoist_syncer.rd_token import RaindropAccessTokenRefresher
from raindrop_todoist_syncer.env_manage import EnvironmentVariablesFileManager
from raindrop_todoist_syncer.rd_credentials import RaindropCredentialsManager


class RaindropClient:
    """
    A class to handle interactions with the Raindrop.io API.

    The API returns paginated responses of 25 raindrops(rds). 25 is the default. It can
    be increased to 50 (source: https://developer.raindrop.io/v1/raindrops/multiple) but
    was unreliable in limited testing.

    Attributes:
        BASE_URL (str)           : API uri
        RAINDROPS_PER_PAGE (int) : total rds per paginated page
        MAX_ALLOWED_PAGES (int)  : arbitrary fallback to prevent infinte loops etc. 200
                                   pages @ 25 rds per page = 5,000 rds

    Example:
    >>> raindrop_client = RaindropClient()
    >>> all_raindrops = raindrop_client.get_all_raindrops()
    """

    BASE_URL = "https://api.raindrop.io/rest/v1"
    RAINDROPS_PER_PAGE = 25
    MAX_ALLOWED_PAGES = 200

    def __init__(self, user_config: UserConfig) -> None:
        """
        Initializes an instance of Raindrop Client.

        Parameters:
            user_config (UserConfig) : User configuration variables

        Instance variables:
            raindrop_access_token (str) : Oauth access token extracted from .env
            headers (dict)             : HTTP request header
        """
        self.user_config = user_config
        self.raindrop_access_token = user_config.raindrop_access_token
        self.headers = {"Authorization": f"Bearer {self.raindrop_access_token}"}
        self._refresh_raindrop_access_token_if_stale()
        logger.info("Raindrop Client initialised")

    def _refresh_raindrop_access_token_if_stale(self) -> None:
        """
        If `stale_token` fetch a new token and update object including headers.
        """
        if self.stale_token():
            rcm = RaindropCredentialsManager(self.user_config)
            evfm = EnvironmentVariablesFileManager(self.user_config)
            ratr = RaindropAccessTokenRefresher(rcm, evfm)
            new_token = ratr.refresh_token_process_runner()
            # Update object with new value
            self.user_config.raindrop_access_token = new_token
            self.raindrop_access_token = new_token
            self.headers = {"Authorization": f"Bearer {self.raindrop_access_token}"}

    def stale_token(self) -> bool:
        """
        Checks the current access token is valid by calling the Raindrop API.

        If the API call succeeds - the token is valid and `stale_token` returns False.
        If the call fails `_core_api_call` raises an error. `stale token` catches the
        error and looks for a 401 status_code. A 401 error indicates the token is stale
        and `stale_token` returns True.

        Any other errors are re-raised for higher level error handling.

        Returns
        -------
        bool
            False if the token is valid (i.e. `stale_token` is False, the token is not
            stale), True if the token is invalid (it's true the token is stale).
        """
        try:
            self._core_api_call(page=0)
        except requests.exceptions.HTTPError as e:
            response = e.response.status_code
            if response != 401:
                raise
            if response == 401:
                logger.warning("Access token is stale.")
                return True
        else:
            logger.info("Access token is valid.")
            return False

    def get_all_raindrops(self) -> List[Dict[str, Any]]:
        """
        Retrieve all raindrops from the Raindrop.io API.

        This is the primary method for fetching and validating raindrops from the API.
        It paginates through the API responses and performs several validation checks
        to ensure the data is consistent.

        Note:
            The `collection_id` defaults to 0, fetching all collections. You can specify
            other collection IDs if needed.

        Returns:
            List        : A list of dictionaries where each dictionary represents a
                          single raindrop. Returns an empty list if no raindrops are
                          found.
        Raises:
            ValueError  : Raised at lower levels, see validator methods in particular.

        Also:
            API Endpoint Documentation: https://developer.raindrop.io/v1/raindrops/multiple.
            Rds are served in pages (default 25).
            Methods structured this way to allow further validation checks etc. to be
            easily added.
        """
        logger.info("Get all raindrops called")
        cumulative_rds = []
        page = 0
        while True:
            response = self._make_api_call(page)
            self._response_validator(response)
            data = response.json()
            if page == 0:
                benchmark_count = self._extract_benchmark_count(data)
                target_pages = self._calculate_max_pages(benchmark_count)
            self._data_validator(data, benchmark_count)
            current_rds = data.get("items", [])
            self._individual_rd_validator(current_rds)
            cumulative_rds.extend(current_rds)
            logger.debug(f"Length of culmative rds: {len(cumulative_rds)}")
            page += 1
            if page >= target_pages:
                logger.debug(f"Page({page}) equals target pages({target_pages})")
                break
        self._cumulative_rds_validator(cumulative_rds, current_rds, benchmark_count)
        logger.info(f"Collected {len(cumulative_rds)} total bookmarks.")
        return cumulative_rds

    def _core_api_call(self, page: int) -> Response:
        """
        Makes the API call to fetch only favourited raindrops.

        Parameters:
            page     : A page to request from the full paginated list.

        Returns:
            response : The API response
        """
        collection_id = 0
        params = {"perpage": self.RAINDROPS_PER_PAGE, "page": page, "search": "❤️"}
        response = requests.get(
            f"{self.BASE_URL}/raindrops/{collection_id}/",
            headers=self.headers,
            params=params,
        )
        response.raise_for_status()
        return response

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def _make_api_call(self, page: int) -> Response:
        """
        A retry logic wrapper for the core API caller.

        The retry logic makes three calls with increasing waits. If the headers contain
        rate limit status - this is logged. NOTE: 200 responses should contain headers,
        but this is not currently enforced.

        Parameters:
            page     : A page to request from the full paginated list.

        Returns:
            response : The API response
        """
        response = self._core_api_call(page)
        if (
            "x-ratelimit-remaining" in response.headers
            and "x-ratelimit-limit" in response.headers
        ):
            logger.debug(
                f"API calls remaining before reset: {response.headers['x-ratelimit-remaining']}/{response.headers['x-ratelimit-limit']}"
            )
        else:
            logger.warning("API headers does not include rate limit status.")
        return response

    def _response_validator(self, response: Response) -> None:
        """
        --DEPRECATED-- Validation for the response status.

        Now replaced with raise_for_status() in _make_api_call. Kept to faciliate any
        additional response validation required in future.
        """
        pass

    def _extract_benchmark_count(self, data: Dict[str, Any]) -> int:
        """
        Extract and store the "benchmark" total of the user's rds on the server.

        This method captures the benchmark from the first API call. This total could
        could change if the user adds or removes rds during the collection process. Or
        with an error.

        Parameters:
            data       : The JSON output from the response i.e. response.json()

        Raises:
            ValueError : If no 'count' field is found, if the value of 'count' is None
                         or the value is negative.
        """
        count = data.get("count")
        logger.debug(f"Benchmark count value: {count}")
        if count is None:
            if "count" in data:
                raise ValueError(
                    "The 'count' key was found in the response data, but its value was None."
                )
            else:
                raise ValueError("The 'count' key was not found in the response data.")
        if count < 0:
            raise ValueError(
                "The 'count' key was found in the response data, but it's value was negative."
            )
        return count

    def _calculate_max_pages(self, benchmark_rd_count: int) -> int:
        """
        Calculates how many api calls are required to collect all rds.

        This takes the benchmark_rd_count (the total rds expected) and divides it by
        the constant RAINDROPS_PER_PAGE. This is passed back to `get_all_raindrops` as
        `target_pages` which sets the number of calls to make to the API.

        NOTE: This should not allow for any infinite loops. Divmod works correctly for
        0, 1, etc. Negative benchmark counts raise an error. MAX_ALLOWED_PAGES caps
        calls even if raindrop.io were to pass a huge benchmark count.

        Parameters:
            benchmark_rd_count  : the users total rds on the raindrop.io server

        Returns:
            max_pages:          : the total number of pages required to call
        """
        max_pages, remainder = divmod(benchmark_rd_count, self.RAINDROPS_PER_PAGE)
        logger.debug(f"Max pages, remainder: {max_pages, remainder}")
        if remainder:
            max_pages += 1
        if max_pages > self.MAX_ALLOWED_PAGES:
            raise ValueError(
                "Max pages greater than allowed. Adjust setting in class constant to override."
            )
        return max_pages

    def _data_validator(self, data: Dict[str, Any], benchmark_count: int) -> None:
        """
        Validate the json output from a Raindrop api response.

        Takes the full JSON and checks:
            - the 'count' in the current response matches the 'benchmark_count' (the
              'count' in the first API response in the current operation).

        Parameters:
            data       : The JSON output from the response i.e. response.json()

        Raises:
            ValueError : If the current 'count' doesn't match the 'benchmark' count.
        """
        if data.get("result") is not True:
            raise ValueError("API Result False")

        new_count = data.get("count")
        logger.debug(f"Count in current response: {new_count} (vs. {benchmark_count})")
        if new_count != benchmark_count:
            raise ValueError(
                f"Count changed during process. Benchmark count: {benchmark_count}. New count: {new_count}."
            )

    def _individual_rd_validator(self, rds: List[Dict[str, Any]]) -> None:
        """
        Validate individual rds returned by the Raindrop API.

        Takes a list of rds (typically of per page length) and checks:
            - "_id" is not len(9) : Logs a warning
            - "_id" is None       : Raises a ValueError
            - "_id" is not an int : Raises a ValueError

        TODO: Monitor. This may be overkill. The API docs don't specify these
        TODO: requirements, but logically they should apply.
        """
        for rd in rds:
            if len(str(rd.get("_id"))) != 9:
                logger.warning(
                    f"Raindrop with _id {rd.get('_id')} does not have 9 chars."
                )

        if any(rd.get("_id") is None for rd in rds):
            raise ValueError(
                f"Invalid raindrop item found in current collection: _id is None.\nRaindrop: {rd}"
            )

        if any(not isinstance(rd.get("_id"), int) for rd in rds):
            raise ValueError(
                f"Invalid raindrop item found in current collection: _id is not of type int.\nRaindrop: {rd}"
            )

        logger.debug(f"Current rds (validated): {len(rds)}")

    def _cumulative_rds_validator(
        self,
        cumulative_rds: List[Dict[str, Any]],
        current_rds: List[Dict[str, Any]],
        benchmark_count: int,
    ) -> None:
        """
        Checks the expected total rds were collected, and in the correct order.

        The rds are collected together, 25 by 25 (or RAINDROPS_PER_PAGE), like animals
        boarding Noah's Ark.

        Current checks:
            - the total number of collected rds matches the benchmark total.
            - checks the rds were collected in the correct order, e.g. by page, 25, 25,
              3, and not 25, 3, 25.

        Returns:
            None:  returns None if data is valid

        Raises:
            ValueError:
                - If the total number of collected raindrops doesn't match the expected
                  benchmark count.
                - If the number of raindrops on the last page does not match the
                  expected length of the last page.
        """
        if len(cumulative_rds) != benchmark_count:
            raise ValueError("Total raindrops extracted not expected length.")

        expected_len_last_page = benchmark_count % self.RAINDROPS_PER_PAGE
        if len(current_rds) != expected_len_last_page:
            raise ValueError(
                f"Last page results not expected length. Expected: {expected_len_last_page}, Got: {len(current_rds)}"
            )
