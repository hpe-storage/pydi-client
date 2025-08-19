# Copyright Hewlett Packard Enterprise Development LP

import pytest
import httpx
from httpx import Response as HTTPXResponse
from http import HTTPStatus
from pydi_client.api.search import SimilaritySearchAPI
from pydi_client.errors import SimilaritySearchFailureException

from pydi_client.sessions.session import Session


@pytest.fixture
def mock_session(mocker):
    # Mock the regular Session
    return mocker.MagicMock(spec=Session)


@pytest.fixture
def similarity_search_api(mock_session):
    return SimilaritySearchAPI(session=mock_session)


def test_search_success(mocker, mock_session, similarity_search_api):

    mock_response = mocker.MagicMock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.json.return_value = {
        "success": True,
        "message": "Similarity search completed successfully.",
        "results": [{"score": 0.9, "dataChunk": "example_data", "chunkMetadata": {}}],
    }

    # Mock execute_with_retry
    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.search.execute_with_retry", return_value=mock_response
    )

    # Configure mock_session to return the mock_response
    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    # Call the method
    result = similarity_search_api.search(
        collection_name="test_collection",
        query="test_query",
        access_key="test_access_key",
        secret_key="test_secret_key",
        top_k=5,
        search_parameters={"param1": "value1"},
    )

    # Assertions
    assert result[0] == {"score": 0.9, "dataChunk": "example_data", "chunkMetadata": {}}
    mock_execute_with_retry.assert_called_once()


def test_search_failure(mocker, mock_session, similarity_search_api):

    mock_response = mocker.MagicMock()
    mock_response.status_code = HTTPStatus.BAD_REQUEST
    mock_response.text = "Bad Request"

    # Mock execute_with_retry
    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.search.execute_with_retry", return_value=mock_response
    )

    # Configure mock_session to return the mock_response
    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    # Call the method and expect an exception
    with pytest.raises(SimilaritySearchFailureException) as exc_info:
        similarity_search_api.search(
            collection_name="test_collection",
            query="test_query",
            access_key="test_access_key",
            secret_key="test_secret_key",
            top_k=5,
            search_parameters={"param1": "value1"},
        )

    # Assertions
    assert "Similarity search failed with status code 400: Bad Request" in str(
        exc_info.value
    )
    mock_execute_with_retry.assert_called_once()


def test_search_invalid_parameters(mock_session, similarity_search_api):

    # Call the method with invalid parameters and expect an exception
    with pytest.raises(TypeError):
        similarity_search_api.search(
            query="test_query",
            access_key="test_access_key",
            secret_key="test_secret_key",
            top_k=5,
            search_parameters={"param1": "value1"},
        )


def test_search_no_results(mocker, similarity_search_api):
    # Mock response without "results"
    mock_response = mocker.MagicMock()
    mock_response.status_code = HTTPStatus.OK
    mock_response.json.return_value = {
        "success": True,
        "message": "No results found",
    }

    # Mock execute_with_retry to return the mock response
    mocker.patch(
        "pydi_client.api.search.execute_with_retry", return_value=mock_response
    )

    # Call the search method
    result = similarity_search_api.search(
        collection_name="test_collection",
        query="test_query",
        access_key="test_access_key",
        secret_key="test_secret_key",
        top_k=5,
        search_parameters={"param1": "value1"},
    )

    # Assert that the result is an empty list
    assert result == []
