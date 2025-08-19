# Copyright Hewlett Packard Enterprise Development LP

import pytest
import httpx
from httpx import Response as HTTPXResponse
from http import HTTPStatus
from pydi_client.api.collection import CollectionAPI
from pydi_client.data.collection_manager import (
    V1CollectionResponse,
    ListCollection,
    ListPipelines,
)
from pydi_client.data.pipeline import BucketUpdateResponse
from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.errors import HTTPUnauthorizedException, UnexpectedStatus

from pydi_client.sessions.session import Session

# filepath: di/sdk/tests/test_collection_api.py


@pytest.fixture
def mock_authsession(mocker):
    # Mock the AuthenticatedSession
    return mocker.MagicMock(spec=AuthenticatedSession)


@pytest.fixture
def mock_session(mocker):
    # Mock the regular Session
    return mocker.MagicMock(spec=Session)


@pytest.fixture
def collection_api(mock_session):
    # Create an instance of CollectionAPI with the mocked session
    return CollectionAPI(session=mock_session)


def test_get_collections_success(mocker, mock_session, collection_api):
    # Mock a successful response
    mock_response = HTTPXResponse(
        status_code=httpx.codes.OK,
        json=[
            {"id": "1", "name": "collection1"},
            {"id": "2", "name": "collection2"},
            {"id": "3", "name": "collection3"},
        ],
    )
    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    # Configure mock_session to return the mock_response
    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    # Call the method
    result = collection_api.get_collections()

    # Assertions
    assert isinstance(result, ListCollection)
    assert result.root[0].name == "collection1"
    assert result.root[0].id == "1"
    assert result.root[1].name == "collection2"
    assert result.root[2].name == "collection3"

    mock_execute_with_retry.assert_called_once()


def test_get_collections_unauthorized(mocker, mock_session, collection_api):
    # Mock an unauthorized response
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    # Configure mock_session to return the mock_response
    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    # Call the method and expect an exception
    with pytest.raises(HTTPUnauthorizedException):
        collection_api.get_collections()


def test_get_collections_unexpected_status(mocker, mock_session, collection_api):
    # Mock an unexpected status code
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    # Configure mock_session to return the mock_response
    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    # Call the method and expect an exception
    with pytest.raises(UnexpectedStatus):
        collection_api.get_collections()


def test_get_collection_success(mocker, mock_session, collection_api):
    # Mock a successful response
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "Test Collection",
            "buckets": ["bucket1", "bucket2"],
            "pipeline": "default_pipeline",
        },
    )
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    # Configure mock_session to return the mock_response
    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    # Call the method
    result = collection_api.get_collection(name="Test Collection")

    # Assertions
    assert isinstance(result, V1CollectionResponse)
    assert result.name == "Test Collection"
    assert result.pipeline == "default_pipeline"
    assert result.buckets == ["bucket1", "bucket2"]


def test_get_collection_unauthorized(mocker, mock_session, collection_api):
    # Mock an unauthorized response
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    # Configure mock_session to return the mock_response
    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    # Call the method and expect an exception
    with pytest.raises(HTTPUnauthorizedException):
        collection_api.get_collection(name="Test Collection")


def test_get_collection_unexpected_status(mocker, mock_session, collection_api):
    # Mock an unexpected status code
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    # Configure mock_session to return the mock_response
    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    # Call the method and expect an exception
    with pytest.raises(UnexpectedStatus):
        collection_api.get_collection(name="Test Collection")


def test_create_collection_success(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "Test Collection",
            "pipeline": "default_pipeline",
            "buckets": ["bucket1", "bucket2"],
        },
    )
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = collection_api.create_collection(
        name="Test Collection",
        pipeline="default_pipeline",
        buckets=["bucket1", "bucket2"],
    )

    assert isinstance(result, V1CollectionResponse)
    assert result.name == "Test Collection"
    assert result.pipeline == "default_pipeline"
    assert result.buckets == ["bucket1", "bucket2"]


def test_create_collection_unauthorized(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        collection_api.create_collection(
            name="Test Collection",
            pipeline="default_pipeline",
            buckets=["bucket1", "bucket2"],
        )


def test_create_collection_unexpected_status(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        collection_api.create_collection(
            name="Test Collection",
            pipeline="default_pipeline",
            buckets=["bucket1", "bucket2"],
        )


def test_delete_collection_success(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.OK)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = collection_api.delete_collection(name="Test Collection")

    assert result is None


def test_delete_collection_unauthorized(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        collection_api.delete_collection(name="Test Collection")


def test_delete_collection_unexpected_status(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        collection_api.delete_collection(name="Test Collection")


def test_assign_buckets_to_collection_success(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={"success": True, "message": "Buckets assigned successfully"},
    )
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = collection_api.assign_buckets_to_collection(
        collection_name="Test Collection", buckets=["bucket1", "bucket2"]
    )

    assert isinstance(result, BucketUpdateResponse)
    assert result.success == True
    assert result.message == "Buckets assigned successfully"


def test_assign_buckets_to_collection_unauthorized(
    mocker, mock_session, collection_api
):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        collection_api.assign_buckets_to_collection(
            collection_name="Test Collection", buckets=["bucket1", "bucket2"]
        )


def test_assign_buckets_to_collection_unexpected_status(
    mocker, mock_session, collection_api
):
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        collection_api.assign_buckets_to_collection(
            collection_name="Test Collection", buckets=["bucket1", "bucket2"]
        )


def test_unassign_buckets_from_collection_success(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={"success": True, "message": "Buckets unassigned successfully"},
    )
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = collection_api.unassign_buckets_from_collection(
        collection_name="Test Collection", buckets=["bucket1", "bucket2"]
    )

    assert isinstance(result, BucketUpdateResponse)
    assert result.success
    assert result.message == "Buckets unassigned successfully"


def test_unassign_buckets_from_collection_unauthorized(
    mocker, mock_session, collection_api
):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        collection_api.unassign_buckets_from_collection(
            collection_name="Test Collection", buckets=["bucket1", "bucket2"]
        )


def test_unassign_buckets_from_collection_unexpected_status(
    mocker, mock_session, collection_api
):
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        collection_api.unassign_buckets_from_collection(
            collection_name="Test Collection", buckets=["bucket1", "bucket2"]
        )
