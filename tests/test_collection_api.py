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
from pydi_client.data.pipeline import BucketUpdateResponse, SourceUpdateResponse
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
    assert result.outputStore is None


def test_create_transcribe_collection_success(mocker, mock_session, collection_api):
    """Test creating a transcribe collection with outputStore parameter."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "transcribe_collection_test",
            "pipeline": "transcribe-image-metadata",
            "buckets": ["test-bucket-1"],
            "outputStore": "test-bucket-1",
            "indexingMode": "",
        },
    )
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = collection_api.create_collection(
        name="transcribe_collection_test",
        pipeline="transcribe-image-metadata",
        buckets=["test-bucket-1"],
        output_store="test-bucket-1",
    )

    assert isinstance(result, V1CollectionResponse)
    assert result.name == "transcribe_collection_test"
    assert result.pipeline == "transcribe-image-metadata"
    assert result.buckets == ["test-bucket-1"]
    assert result.outputStore == "test-bucket-1"


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


def test_create_collection_with_paths(mocker, mock_session, collection_api):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.CREATED,
        json={
            "name": "fs_collection",
            "pipeline": "default_pipeline",
            "buckets": [],
            "paths": ["/file/fs1/docs"],
        },
    )
    mock_execute = mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    result = collection_api.create_collection(
        name="fs_collection",
        pipeline="default_pipeline",
        buckets=None,
        paths=["/file/fs1/docs"],
    )

    sent = mock_execute.call_args.kwargs
    assert sent["method"] == "post"
    assert sent["url"] == "/api/v1/collections"
    assert sent["json"] == {
        "name": "fs_collection",
        "pipeline": "default_pipeline",
        "paths": ["/file/fs1/docs"],
    }
    assert isinstance(result, V1CollectionResponse)
    assert result.paths == ["/file/fs1/docs"]


def test_create_collection_without_paths_omits_paths(
    mocker, mock_session, collection_api
):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.CREATED,
        json={"name": "c1", "pipeline": "p1", "buckets": ["bucket1"]},
    )
    mock_execute = mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    result = collection_api.create_collection(
        name="c1", pipeline="p1", buckets=["bucket1"]
    )

    assert "paths" not in mock_execute.call_args.kwargs["json"]
    assert result.paths is None


def test_admin_create_collection_with_paths_omits_buckets(mocker):
    from pydi_client import DIAdminClient

    mocker.patch("pydi_client.api.auth.AuthAPI.login", return_value=mocker.MagicMock())
    admin = DIAdminClient(uri="https://di.example.com", username="admin", password="pass")
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.CREATED,
        json={"name": "fs_collection", "pipeline": "p1", "paths": ["/file/fs1/docs"]},
    )
    mock_execute = mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    admin.create_collection(
        name="fs_collection", pipeline="p1", paths=["/file/fs1/docs"]
    )

    sent_json = mock_execute.call_args.kwargs["json"]
    assert "buckets" not in sent_json
    assert sent_json["paths"] == ["/file/fs1/docs"]


def test_admin_create_collection_without_sources_sends_empty_buckets(mocker):
    from pydi_client import DIAdminClient

    mocker.patch("pydi_client.api.auth.AuthAPI.login", return_value=mocker.MagicMock())
    admin = DIAdminClient(uri="https://di.example.com", username="admin", password="pass")
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.CREATED,
        json={"name": "c1", "pipeline": "p1", "buckets": []},
    )
    mock_execute = mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    admin.create_collection(name="c1", pipeline="p1")

    sent_json = mock_execute.call_args.kwargs["json"]
    assert sent_json["buckets"] == []
    assert "paths" not in sent_json


@pytest.mark.parametrize(
    "method_name, endpoint",
    [
        ("assign_sources_to_collection", "assignSources"),
        ("unassign_sources_from_collection", "unassignSources"),
    ],
)
def test_sources_to_collection_success(
    mocker, mock_session, collection_api, method_name, endpoint
):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={"success": True, "message": "Sources updated successfully"},
    )
    mock_execute = mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    result = getattr(collection_api, method_name)(
        collection_name="my_collection", paths=["/file/fs1/docs"]
    )

    sent = mock_execute.call_args.kwargs
    assert sent["method"] == "post"
    assert sent["url"] == f"/api/v1/collections/my_collection/{endpoint}"
    assert sent["json"] == {"paths": ["/file/fs1/docs"]}
    assert isinstance(result, SourceUpdateResponse)
    assert result.success
    assert result.message == "Sources updated successfully"


@pytest.mark.parametrize(
    "method_name", ["assign_sources_to_collection", "unassign_sources_from_collection"]
)
def test_sources_to_collection_unauthorized(
    mocker, mock_session, collection_api, method_name
):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    with pytest.raises(HTTPUnauthorizedException):
        getattr(collection_api, method_name)(
            collection_name="my_collection", paths=["/file/fs1/docs"]
        )


@pytest.mark.parametrize(
    "method_name", ["assign_sources_to_collection", "unassign_sources_from_collection"]
)
@pytest.mark.parametrize(
    "status", [HTTPStatus.CONFLICT, HTTPStatus.INTERNAL_SERVER_ERROR]
)
def test_sources_to_collection_unexpected_status(
    mocker, mock_session, collection_api, method_name, status
):
    mock_response = HTTPXResponse(status_code=status)
    mocker.patch(
        "pydi_client.api.collection.execute_with_retry", return_value=mock_response
    )

    with pytest.raises(UnexpectedStatus):
        getattr(collection_api, method_name)(
            collection_name="my_collection", paths=["/file/fs1/docs"]
        )


@pytest.mark.parametrize(
    "method_name", ["assign_sources_to_collection", "unassign_sources_from_collection"]
)
def test_admin_client_sources_signature(method_name):
    import inspect
    from pydi_client import DIAdminClient

    sig = inspect.signature(getattr(DIAdminClient, method_name))
    for param in ("collection_name", "paths"):
        assert sig.parameters[param].kind == inspect.Parameter.KEYWORD_ONLY
