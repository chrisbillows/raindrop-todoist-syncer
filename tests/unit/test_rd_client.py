import random
from unittest.mock import patch, Mock
from urllib import response

import pytest
from requests import HTTPError
import tenacity

# from raindrop import RaindropClient
from raindrop import RaindropClient_dev
from tests.conftest import response_one_data, response_two_data


@pytest.fixture
def rd_client():
    # return RaindropClient()
    return RaindropClient_dev()


class TestInit:
    def test_api_url(self, rd_client):
        # assert rd_client.API_URL == "https://api.raindrop.io/rest/v1"
        assert rd_client.BASE_URL == "https://api.raindrop.io/rest/v1"

    def test_oauth_token(self, rd_client):
        assert rd_client.raindrop_oauth_token != None

    def test_headers(self, rd_client):
        assert rd_client.headers != None

    def test_header_structure_key_is_authorization(self, rd_client):
        # headers = rd_client._make_headers()
        headers = rd_client.headers
        assert list(headers.keys())[0] == "Authorization"

    def test_header_structure__value_starts_bearer(self, rd_client):
        headers = rd_client.headers
        assert str(list(headers.values())[0]).startswith("Bearer") == True


class TestGetAllRaindrops:

    def test_get_all_raindrops_len(self, mock_requests_get, rd_client):
        result = rd_client.get_all_raindrops()
        assert len(result) == 26

    def test_get_all_raindrops_type(self, mock_requests_get, rd_client):
        result = rd_client.get_all_raindrops()
        assert type(result) == list

    def test_get_all_raindrops_ids(self, mock_requests_get, rd_client):
        expected_ids = [
            628161680, 628161679, 628161678, 628161677, 628161676, 628161675, 628161674,
            628161673, 628161672, 628161671, 628161670, 628161669, 628161668, 628161667,
            628161666, 628161665, 628161664, 628161663, 628161662, 628161661, 628161660,
            628161659, 628161658, 628161657, 628161656, 628161655]
        result = rd_client.get_all_raindrops()
        ids = [x['_id'] for x in result]
        assert ids == expected_ids


class TestCoreApiCall:
    """
    Tests for the core API call, without tenacity's retries, waits etc.
    """
    @pytest.mark.parametrize("page", [0, 1])
    def test__core_api_call_cached_responses_not_none(
        self, mock_requests_get, rd_client, page
    ):
        response = rd_client._core_api_call(page)
        assert response is not None

    @pytest.mark.parametrize("page", [0, 1])
    def test__core_api_call_cached_responses_status_200(
        self, mock_requests_get, rd_client, page
    ):
        response_status = rd_client._core_api_call(page).status_code
        assert response_status == 200

    def test_core_api_call_cached_responses_missing_pg_exception(
        self, mock_requests_get, rd_client
    ):
        with pytest.raises(HTTPError):
            rd_client._core_api_call(10).status_code
          
    
    @pytest.mark.parametrize(
    "page, key_path, expected_value",
    [
        (0, ["result"], True),
        (1, ["result"], True),
        (0, ["items", 0, "creatorRef", "name"], "christopherbillows"),
        (1, ["items", 0, "creatorRef", "name"], "christopherbillows"),
        (0, ["count"], 26),
        (1, ["count"], 26),
        (0, ["collectionId"], 36697540),
        (1, ["collectionId"], 36697540),
    ],
    )
    def test_core_call_cached_responses(self, 
    mock_requests_get, rd_client, page, key_path, expected_value
    ):
        response = rd_client._core_api_call(page)
        json_data = response.json()
        for key in key_path:
            json_data = json_data[key]
        assert json_data == expected_value


class TestMakeApiCall:
    """
    Tests for the full API call, including the tenacity retry logic.
    """

    @pytest.mark.parametrize("page", [0, 1])
    def test__make_api_call_cached_responses_not_none(
        self, mock_requests_get, rd_client, page
    ):
        response = rd_client._make_api_call(page)
        assert response is not None

    @pytest.mark.parametrize("page", [0, 1])
    def test__make_api_call_cached_responses_status_200(
        self, mock_requests_get, rd_client, page
    ):
        response_status = rd_client._make_api_call(page).status_code
        assert response_status == 200

    @pytest.mark.parametrize(
    "page, key_path, expected_value",
    [
        (0, ["result"], True),
        (1, ["result"], True),
        (0, ["items", 0, "creatorRef", "name"], "christopherbillows"),
        (1, ["items", 0, "creatorRef", "name"], "christopherbillows"),
        (0, ["count"], 26),
        (1, ["count"], 26),
        (0, ["collectionId"], 36697540),
        (1, ["collectionId"], 36697540),
    ],
    )
    def test_make_api_call_cached_responses(self, 
    mock_requests_get, rd_client, page, key_path, expected_value
    ):
        response = rd_client._make_api_call(page)
        json_data = response.json()
        for key in key_path:
            json_data = json_data[key]
        assert json_data == expected_value    
        
    @pytest.mark.parametrize(
        "status_code, exception, match_str, call_count",
        [
            (200, None, None, 1),                 # 1 call, no retries
            (403, tenacity.RetryError, None, 3),  # 3 retries before raising RetryError
            (404, tenacity.RetryError, None, 3),
            (500, tenacity.RetryError, None, 3),
        ],
    )
    def test_makes_api_call_retries_for_various_status_codes(
        self, mocker, rd_client, status_code, exception, match_str, call_count
    ):
        """ 
        Tests handling of different status codes including retry logic.
        """
        mock_response = Mock()
        mock_response.status_code = status_code
        if status_code != 200:
            mock_response.raise_for_status.side_effect = HTTPError(
                f"API Error: {status_code}"
            )
        mock_get = mocker.patch("requests.get")
        mock_get.return_value = mock_response
        if exception:
            with pytest.raises(exception, match=match_str):
                rd_client._make_api_call(0)
            assert mock_get.call_count == call_count
        else:
            assert rd_client._make_api_call(0) == mock_response
            assert mock_get.call_count == call_count


# @pytest.mark.parametrize(
#     "status_code, exception, match_str",
#     [
#         (200, None, None),
#         (403, ValueError, "API Error: 403"),
#         (404, ValueError, "API Error: 404"),
#         (500, ValueError, "API Error: 500"),
#     ],
# )
# def test__response_validator(self, rd_client, status_code, exception, match_str):
#     """

#     """
#     mock_response = Mock()
#     mock_response.status_code = status_code
#     if exception:
#         with pytest.raises(exception, match=match_str):
#             rd_client._response_validator(mock_response)
#     else:
#         assert rd_client._response_validator(mock_response) is None


class TestExtractBenchmarkCount:

    @pytest.mark.parametrize("fixture_name", ["response_one_data", "response_two_data"])
    def test_extract_benchmark_count(self, request, rd_client, fixture_name):
        data = request.getfixturevalue(fixture_name)
        benchmark_count = rd_client._extract_benchmark_count(data)
        assert benchmark_count == 26

    def test_extract_benchmark_count_700(self, rd_client):
        data = {"count": 700}
        benchmark_count = rd_client._extract_benchmark_count(data)
        assert benchmark_count == 700

    def test_extract_benchmark_set_to_none(self, rd_client):
        data = {"count": None}
        with pytest.raises(
            ValueError,
            match="The 'count' key was found in the response data, but its value was None.",
        ):
            rd_client._extract_benchmark_count(data)

    def test_extract_benchmark_count_not_present(self, rd_client):
        data = {}
        with pytest.raises(
            ValueError, match="The 'count' key was not found in the response data."
        ):
            rd_client._extract_benchmark_count(data)


class TestCalculateMaxPages:

    def test_calculate_max_pages_response_one(self, rd_client, response_one_data):
        benchmark_rd_count = response_one_data["count"]
        assert rd_client._calculate_max_pages(benchmark_rd_count) == 2

    def test_calculate_max_pages_random_allowable_num(self, rd_client):
        max_rds = rd_client.MAX_ALLOWED_PAGES * rd_client.RAINDROPS_PER_PAGE
        benchmark_rd_count = random.randint(1, max_rds)
        whole_pages = benchmark_rd_count // rd_client.RAINDROPS_PER_PAGE
        partial_pages = benchmark_rd_count % rd_client.RAINDROPS_PER_PAGE
        if partial_pages:
            whole_pages += 1
        assert rd_client._calculate_max_pages(benchmark_rd_count) == whole_pages

    def test_calculate_max_pages_error(self, rd_client):
        benchmark_rd_count = (
            rd_client.MAX_ALLOWED_PAGES * rd_client.RAINDROPS_PER_PAGE + 1
        )
        with pytest.raises(
            ValueError,
            match="Max pages greater than allowed. Adjust setting in class constant to override.",
        ):
            rd_client._calculate_max_pages(benchmark_rd_count)


class TestDataValidator:

    def test_data_validator_result_true(self, rd_client, response_one_data):
        assert rd_client._data_validator(response_one_data, 26) == None

    def test_data_validator_result_false(self, rd_client):
        data = {"result": False}
        with pytest.raises(ValueError, match="API Result False"):
            rd_client._data_validator(data, 26)

    def test_data_validator_benchmark_count_change(self, rd_client, response_one_data):
        benchmark_rd_count = 30
        new_count = response_one_data["count"]
        with pytest.raises(
            ValueError,
            match=f"Count changed during process. Benchmark count: {benchmark_rd_count}. New count: {new_count}.",
        ):
            rd_client._data_validator(response_one_data, benchmark_rd_count)


class TestsIndividualRdValidator:

    @pytest.mark.parametrize("fixture_name", ["response_one_data", "response_two_data"])
    def test__individual_rd_validator(self, request, rd_client, fixture_name):
        data = request.getfixturevalue(fixture_name)
        rds = data["items"]
        assert rd_client._individual_rd_validator(rds) is None

    def test__individual_rd_validator_manual_ids_pass(self, rd_client):
        rds = [{"_id": 123}, {"_id": 456}, {"_id": 789}]
        assert rd_client._individual_rd_validator(rds) is None

    @pytest.mark.parametrize(
        "rds, match_str",
        [
            (
                [{"_id": None}, {"_id": 456}, {"_id": 789}],
                "Invalid raindrop item found in current collection.",
            ),
            (
                [{"_id": 123}, {"_id": 456}, {"other_key": "other_value"}],
                "Invalid raindrop item found in current collection.",
            ),
        ],
    )
    def test__individual_rd_validator_manual_ids_fails(self, rd_client, rds, match_str):
        rds = rds
        with pytest.raises(ValueError, match=match_str):
            rd_client._individual_rd_validator(rds)

    # def test__individual_rd_validator_manual_ids_fail_empty(self, rd_client):
    #     #TODO: There are two tests commented out here. They test 
          #TODO         a) if the id is blank
          #TODO         b) if the id is 9 digits
          
          #TODO  Currently the individual_rd_validator does NOT check for this.
          
          #TODO  We need to decide to either:
          #TODO       1) Build in the check and raise error, but are these errors "enough"
          #TODO       2) Log it as a warning only
          #TODO       3) Discard completely
    #     rds = [{"_id": ""}, {"_id": 456}, {"_id": 789}]
    #     with pytest.raises(
    
    #         rd_client._individual_rd_validator(rds)

    # def test__individual_rd_validator_manual_ids_not_9_digits(self, rd_client):
    #     # TODO: Finish
    #     rds = 
    #     with pytest.raises(
    #         ValueError, match="Invalid raindrop item found in current collection."
    #     ):
    #         rd_client._individual_rd_validator(rds)


class TestCumulativeRdsValidator:

    @pytest.mark.parametrize(
        "benchmark_count, exception, match_str",
        [
            (26, None, None),
            (27, ValueError, "Total raindrops extracted not expected length."),
        ],
    )
    def test_cumulative_rds_validator(
        self,
        rd_client,
        exception,
        match_str,
        response_one_data,
        response_two_data,
        benchmark_count,
    ):
        current_rds = response_two_data["items"]
        cumulative_rds = response_one_data["items"] + current_rds
        bmc = benchmark_count
        if exception is not None:
            with pytest.raises(exception, match=match_str):
                rd_client._cumulative_rds_validator(cumulative_rds, current_rds, bmc)
        else:
            assert (
                rd_client._cumulative_rds_validator(cumulative_rds, current_rds, bmc)
                is None
            )

    def test_cumulative_rds_validator_manual_pass(self, rd_client):
        cumulative_rds = list(range(1772))
        current_rds = list(range(22))
        bm = 1772
        assert (
            rd_client._cumulative_rds_validator(cumulative_rds, current_rds, bm) is None
        )

    def test_cumulative_rds_validator_manual_fail(self, rd_client):
        cumulative_rds = list(range(1772))
        current_rds = list(range(22))
        bm = 1771
        with pytest.raises(
            ValueError, match="Total raindrops extracted not expected length."
        ):
            rd_client._cumulative_rds_validator(cumulative_rds, current_rds, bm)

    def test_cumulative_rds_last_pg_wrong_length(self, rd_client):
        cumulative_rds = list(range(53))
        current_rds = list(range(25))
        bm = 53
        expected_len_last_page = bm % rd_client.RAINDROPS_PER_PAGE
        with pytest.raises(
            ValueError,
            match=f"Last page results not expected length. Expected: {expected_len_last_page}, Got: {len(current_rds)}",
        ):
            rd_client._cumulative_rds_validator(cumulative_rds, current_rds, bm)
