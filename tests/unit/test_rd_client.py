import random
from unittest import mock
from urllib import response
import pytest

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


# class TestGetAllRaindrops:

#     def test_get_all_raindrops_len(self, mock_requests_get, rd_client):
#         result = rd_client.get_all_raindrops()
#         assert len(result) == 26

#     def test_get_all_raindrops_len(self, mock_requests_get, rd_client):
#         rd_client = RaindropClient()
#         result = rd_client.get_all_raindrops()
#         assert type(result) == list

#     def test_get_all_raindrops_ids(self, mock_requests_get, rd_client):
#         expected_ids = [
#             628161680, 628161679, 628161678, 628161677, 628161676, 628161675, 628161674,
#             628161673, 628161672, 628161671, 628161670, 628161669, 628161668, 628161667,
#             628161666, 628161665, 628161664, 628161663, 628161662, 628161661, 628161660,
#             628161659, 628161658, 628161657, 628161656, 628161655]
#         result = rd_client.get_all_raindrops()
#         ids = [x['_id'] for x in result]
#         assert ids == expected_ids


class TestDev:
    """
    Additional test for refactored RaindropClass

    To be combined with other tests once everything works correctly.
    """

    @pytest.mark.parametrize("page", [0, 1, 2])
    def test__make_api_call_not_none(self, mock_requests_get, rd_client, page):
        response = rd_client._make_api_call(page)
        assert response is not None

    @pytest.mark.parametrize("page", [0, 1])
    def test__make_api_call_status_200(self, mock_requests_get, rd_client, page):
        response_status = rd_client._make_api_call(page).status_code
        assert response_status == 200

    def test__make_api_call_status_404(self, mock_requests_get, rd_client):
        response_status = rd_client._make_api_call(2).status_code
        assert response_status == 404

    @pytest.mark.parametrize(
        "status_code, exception, match_str",
        [
            (200, None, None),
            (403, ValueError, "API Error: 403"),
            (404, ValueError, "API Error: 404"),
            (500, ValueError, "API Error: 500"),
        ],
    )
    def test__response_validator(self, rd_client, status_code, exception, match_str):
        mock_response = mock.Mock()
        mock_response.status_code = status_code
        if exception:
            with pytest.raises(exception, match=match_str):
                rd_client._response_validator(mock_response)
        else:
            assert rd_client._response_validator(mock_response) is None

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
``
    # def test__individual_rd_validator_manual_ids_fail_empty(self, rd_client):
    #     rds = [{"_id": ""}, {"_id": 456}, {"_id": 789}]
    #     #! Don't we want this to fail?
    #     #! Why **am** I testing this??
    #     with pytest.raises(
    #         ValueError, match="Invalid raindrop item found in current collection."
    #     ):
    #         rd_client._individual_rd_validator(rds)

    def test__individual_rd_validator_manual_ids_fail_none(self, rd_client):
        rds = [{"_id": None}, {"_id": 456}, {"_id": 789}]
        with pytest.raises(
            ValueError, match="Invalid raindrop item found in current collection."
        ):
            rd_client._individual_rd_validator(rds)

    def test__individual_rd_validator_manual_ids_fail_missing(self, rd_client):
        rds = [{"_id": 123}, {"_id": 456}, {"other_key": "other_value"}]
        with pytest.raises(
            ValueError, match="Invalid raindrop item found in current collection."
        ):
            rd_client._individual_rd_validator(rds)

    def test_cumulative_rds_validator(self):
        pass


# def test__make_api_call_response_has_no_status(self, mock_requests_get_no_status, rd_client):
#! Lets just ditch this - I don't even know what I'm trying to do here!
#     response = rd_client._make_api_call(0)
#     with pytest.raises(AttributeError):
#         # _ = response.status_code
#         _ = response.non_existent_attribute
