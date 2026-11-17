# Copyright Hewlett Packard Enterprise Development LP

import pytest
import httpx
from httpx import Response as HTTPXResponse
from http import HTTPStatus
from pydi_client.api import search as search_module
from pydi_client.api.search import SimilaritySearchAPI
from pydi_client.api.utils import execute_with_retry, is_file_user_auth_failure
from pydi_client.di_client import DIClient
from pydi_client.errors import (
    FileUserAuthenticationError,
    FileUserLockoutError,
    HTTPUnauthorizedException,
    SimilaritySearchFailureException,
)

from pydi_client.sessions.authenticated_session import AuthenticatedSession
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


OK_BODY = {"success": True, "message": "ok", "results": []}
FILE_USER_401 = {"status": "Unauthorized", "error": "Invalid file user credentials"}


def _sent_body(execute):
    return execute.call_args.kwargs["json"]


def test_search_with_file_credentials_sends_only_file_credentials(
    mocker, similarity_search_api
):
    execute = mocker.patch(
        "pydi_client.api.search.execute_with_retry",
        return_value=HTTPXResponse(HTTPStatus.OK, json=OK_BODY),
    )

    similarity_search_api.search(
        collection_name="fs_collection",
        query="q",
        top_k=3,
        file_username="alice",
        file_password="alice-pw",
    )

    body = _sent_body(execute)
    assert body["fileCredentials"] == {"username": "alice", "password": "alice-pw"}
    assert "credentials" not in body
    assert execute.call_args.kwargs["refresh_on_unauthorized"] is False


def test_search_with_s3_credentials_payload_is_unchanged(mocker, similarity_search_api):
    execute = mocker.patch(
        "pydi_client.api.search.execute_with_retry",
        return_value=HTTPXResponse(HTTPStatus.OK, json=OK_BODY),
    )

    similarity_search_api.search(
        collection_name="c",
        query="q",
        top_k=3,
        access_key="ak",
        secret_key="sk",
        search_parameters={"metric": "cosine"},
    )

    assert _sent_body(execute) == {
        "collectionName": "c",
        "query": "q",
        "topK": 3,
        "searchParams": {"metric": "cosine"},
        "credentials": {"accessKey": "ak", "secretKey": "sk"},
    }


def test_search_with_both_credential_pairs_sends_both(mocker, similarity_search_api):
    execute = mocker.patch(
        "pydi_client.api.search.execute_with_retry",
        return_value=HTTPXResponse(HTTPStatus.OK, json=OK_BODY),
    )

    similarity_search_api.search(
        collection_name="c",
        query="q",
        top_k=3,
        access_key="ak",
        secret_key="sk",
        file_username="alice",
        file_password="alice-pw",
    )

    body = _sent_body(execute)
    assert body["credentials"] == {"accessKey": "ak", "secretKey": "sk"}
    assert body["fileCredentials"] == {"username": "alice", "password": "alice-pw"}


@pytest.mark.parametrize(
    "credentials, message",
    [
        ({}, "Provide access_key and secret_key"),
        ({"access_key": "ak"}, "access_key and secret_key must be provided together"),
        ({"secret_key": "sk"}, "access_key and secret_key must be provided together"),
        (
            {"file_username": "alice"},
            "file_username and file_password must be provided together",
        ),
        (
            {"file_password": "pw", "access_key": "ak", "secret_key": "sk"},
            "file_username and file_password must be provided together",
        ),
    ],
)
def test_search_rejects_missing_or_incomplete_credentials(
    mocker, similarity_search_api, credentials, message
):
    execute = mocker.patch("pydi_client.api.search.execute_with_retry")

    with pytest.raises(ValueError, match=message):
        similarity_search_api.search(
            collection_name="c", query="q", top_k=3, **credentials
        )

    execute.assert_not_called()


@pytest.mark.parametrize(
    "headers, retry_after",
    [({"Retry-After": "120"}, 120), ({}, None), ({"Retry-After": "soon"}, None)],
)
def test_search_lockout_raises_file_user_lockout_error(
    mocker, similarity_search_api, headers, retry_after
):
    mocker.patch(
        "pydi_client.api.search.execute_with_retry",
        return_value=HTTPXResponse(
            HTTPStatus.TOO_MANY_REQUESTS,
            headers=headers,
            json={
                "status": "Too Many Requests",
                "error": "Too many failed attempts; try again later",
            },
        ),
    )

    with pytest.raises(FileUserLockoutError) as exc_info:
        similarity_search_api.search(
            collection_name="fs",
            query="q",
            top_k=3,
            file_username="alice",
            file_password="wrong",
        )

    assert exc_info.value.retry_after == retry_after
    assert exc_info.value.status_code == 429
    assert isinstance(exc_info.value, SimilaritySearchFailureException)


@pytest.mark.parametrize("session_cls", [Session, AuthenticatedSession])
def test_search_rejected_file_credentials_are_not_retried(mocker, session_cls):
    session = mocker.MagicMock(spec=session_cls)
    request = session.get_httpx_client.return_value.request
    request.return_value = HTTPXResponse(HTTPStatus.UNAUTHORIZED, json=FILE_USER_401)
    refresh = mocker.patch("pydi_client.api.utils.AuthAPI.refresh")

    with pytest.raises(FileUserAuthenticationError) as exc_info:
        SimilaritySearchAPI(session=session).search(
            collection_name="fs",
            query="q",
            top_k=3,
            file_username="alice",
            file_password="wrong",
        )

    assert isinstance(exc_info.value, SimilaritySearchFailureException)
    refresh.assert_not_called()
    assert request.call_count == 1


@pytest.mark.parametrize("session_cls", [Session, AuthenticatedSession])
@pytest.mark.parametrize("status", [HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN])
def test_search_other_auth_failures_do_not_refresh_session(mocker, session_cls, status):
    session = mocker.MagicMock(spec=session_cls)
    request = session.get_httpx_client.return_value.request
    request.return_value = HTTPXResponse(status, json={"status": "Unauthenticated"})
    refresh = mocker.patch("pydi_client.api.utils.AuthAPI.refresh")

    with pytest.raises(SimilaritySearchFailureException) as exc_info:
        SimilaritySearchAPI(session=session).search(
            collection_name="c", query="q", top_k=3, access_key="ak", secret_key="sk"
        )

    assert not isinstance(exc_info.value, FileUserAuthenticationError)
    assert f"status code {int(status)}" in str(exc_info.value)
    refresh.assert_not_called()
    assert request.call_count == 1


def test_search_debug_log_masks_secrets(mocker, similarity_search_api):
    execute = mocker.patch(
        "pydi_client.api.search.execute_with_retry",
        return_value=HTTPXResponse(HTTPStatus.OK, json=OK_BODY),
    )
    debug = mocker.patch.object(search_module.logger, "debug")

    similarity_search_api.search(
        collection_name="c",
        query="q",
        top_k=3,
        access_key="ak",
        secret_key="s3-secret",
        file_username="alice",
        file_password="file-secret",
    )

    logged = " ".join(str(call) for call in debug.call_args_list)
    assert "s3-secret" not in logged
    assert "file-secret" not in logged
    assert "'secretKey': '***'" in logged
    assert "'password': '***'" in logged
    body = _sent_body(execute)
    assert body["credentials"]["secretKey"] == "s3-secret"
    assert body["fileCredentials"]["password"] == "file-secret"


@pytest.mark.parametrize(
    "response, expected",
    [
        (HTTPXResponse(HTTPStatus.UNAUTHORIZED, json=FILE_USER_401), True),
        (HTTPXResponse(HTTPStatus.UNAUTHORIZED, json={"error": "other"}), False),
        (HTTPXResponse(HTTPStatus.UNAUTHORIZED, content=b"not json"), False),
        (HTTPXResponse(HTTPStatus.UNAUTHORIZED, json=["list"]), False),
        (HTTPXResponse(HTTPStatus.FORBIDDEN, json=FILE_USER_401), False),
    ],
)
def test_is_file_user_auth_failure(response, expected):
    assert is_file_user_auth_failure(response) is expected


def test_execute_with_retry_does_not_refresh_on_file_user_401(mocker):
    session = mocker.MagicMock(spec=AuthenticatedSession)
    request = mocker.MagicMock(
        return_value=HTTPXResponse(HTTPStatus.UNAUTHORIZED, json=FILE_USER_401)
    )
    refresh = mocker.patch("pydi_client.api.utils.AuthAPI.refresh")

    with pytest.raises(FileUserAuthenticationError):
        execute_with_retry(
            session=session, request_func=request, method="POST", url="/x"
        )

    refresh.assert_not_called()
    request.assert_called_once_with(method="POST", url="/x")


def test_execute_with_retry_still_refreshes_on_session_401(mocker):
    session = mocker.MagicMock(spec=AuthenticatedSession)
    request = mocker.MagicMock(
        return_value=HTTPXResponse(
            HTTPStatus.UNAUTHORIZED,
            json={
                "status": "HTTPUnauthorized",
                "error": "Authorization header not found",
            },
        )
    )
    refreshed_request = session.get_httpx_client.return_value.request
    refreshed_request.return_value = HTTPXResponse(HTTPStatus.OK, json=OK_BODY)
    refresh = mocker.patch("pydi_client.api.utils.AuthAPI.refresh")

    response = execute_with_retry(
        session=session, request_func=request, method="GET", url="/x"
    )

    assert response.status_code == HTTPStatus.OK
    refresh.assert_called_once_with(session=session)
    refreshed_request.assert_called_once_with(method="GET", url="/x")


def test_execute_with_retry_without_refresh_returns_auth_failure(mocker):
    session = mocker.MagicMock(spec=AuthenticatedSession)
    unauthorized = HTTPXResponse(HTTPStatus.FORBIDDEN, json={"status": "Forbidden"})
    request = mocker.MagicMock(return_value=unauthorized)
    refresh = mocker.patch("pydi_client.api.utils.AuthAPI.refresh")

    response = execute_with_retry(
        session=session,
        request_func=request,
        refresh_on_unauthorized=False,
        method="GET",
        url="/x",
    )

    assert response is unauthorized
    refresh.assert_not_called()
    request.assert_called_once_with(method="GET", url="/x")


def test_execute_with_retry_unauthenticated_session_still_raises(mocker):
    request = mocker.MagicMock(return_value=HTTPXResponse(HTTPStatus.UNAUTHORIZED))

    with pytest.raises(HTTPUnauthorizedException):
        execute_with_retry(
            session=mocker.MagicMock(spec=Session), request_func=request, url="/x"
        )


def test_di_client_similarity_search_passes_file_credentials(mocker):
    search = mocker.patch(
        "pydi_client.di_client.SimilaritySearchAPI.search", return_value=[]
    )

    DIClient(uri="https://di.example.com").similarity_search(
        collection_name="fs",
        query="q",
        top_k=2,
        file_username="alice",
        file_password="alice-pw",
    )

    search.assert_called_once_with(
        query="q",
        collection_name="fs",
        top_k=2,
        access_key=None,
        secret_key=None,
        file_username="alice",
        file_password="alice-pw",
        search_parameters=None,
    )
