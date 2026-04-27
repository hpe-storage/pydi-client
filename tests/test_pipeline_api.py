# Copyright Hewlett Packard Enterprise Development LP

import pytest
from httpx import Response as HTTPXResponse
from http import HTTPStatus
from pydi_client.api.pipeline import PipelineAPI
from pydi_client.api.utils import execute_with_retry
from pydi_client.data.pipeline import V1CreatePipelineResponse, V1DeletePipelineResponse
from pydi_client.data.collection_manager import (
    V1PipelineResponse,
    ListPipelines,
)
from pydi_client.errors import HTTPUnauthorizedException, UnexpectedStatus
from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.sessions.session import Session

# filepath: di/sdk/pydi_client/api/test_pipeline_api.py


@pytest.fixture
def mock_authsession(mocker):
    return mocker.MagicMock(spec=AuthenticatedSession)


@pytest.fixture
def mock_session(mocker):
    return mocker.MagicMock(spec=Session)


@pytest.fixture
def pipeline_api(mock_session):
    return PipelineAPI(session=mock_session)


def test_create_pipeline_success(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={"success": True, "message": "Pipeline created successfully"},
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.create_pipeline(
        name="Test Pipeline",
        pipeline_type="type1",
        model="model1",
        custom_func="func1",
        event_filter_object_suffix=[".txt"],
        event_filter_max_object_size=100,
        schema="schema1",
    )

    assert isinstance(result, V1CreatePipelineResponse)
    assert result.success
    assert result.message == "Pipeline created successfully"


def test_create_pipeline_unauthorized(mocker, mock_authsession, pipeline_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        pipeline_api.create_pipeline(
            name="Test Pipeline",
            pipeline_type="type1",
            model="model1",
            custom_func="func1",
            event_filter_object_suffix=[".txt"],
            event_filter_max_object_size=100,
            schema="schema1",
        )


def test_create_pipeline_unexpected_status(mocker, mock_authsession, pipeline_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        pipeline_api.create_pipeline(
            name="Test Pipeline",
            pipeline_type="type1",
            model="model1",
            custom_func="func1",
            event_filter_object_suffix=[".txt"],
            event_filter_max_object_size=100,
            schema="schema1",
        )


def test_get_pipeline_success(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "Test Pipeline",
            "type": "type1",
            "model": "model1",
            "customFunction": "func1",
            "eventFilter": {"objectSuffix": ".txt"},
            "schema": "schema1",
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.get_pipeline(name="Test Pipeline")

    assert isinstance(result, V1PipelineResponse)
    assert result.name == "Test Pipeline"
    assert result.type == "type1"
    assert result.model == "model1"
    assert result.customFunction == "func1"
    assert result.schema_name == "schema1"
    assert result.eventFilter == {"objectSuffix": ".txt"}
    assert result.prompt is None


def test_create_transcribe_pipeline_success(mocker, mock_session, pipeline_api):
    """Test creating a transcribe-metadata pipeline with prompt parameter."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={"success": True, "message": "transcribe-image-metadata resource created successfully."},
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.create_pipeline(
        name="transcribe-image-metadata",
        pipeline_type="transcribe-metadata",
        model="cosmos-reason2-8b",
        event_filter_object_suffix=["*.jpg", "*.png", "*.jpeg"],
        event_filter_max_object_size=10737418240,
        prompt="Transcribe the image content into text.",
        schema="default-transcribe-metadata-schema",
    )

    assert isinstance(result, V1CreatePipelineResponse)
    assert result.success is True
    assert "transcribe-image-metadata" in result.message


def test_get_transcribe_pipeline_success(mocker, mock_session, pipeline_api):
    """Test retrieving a transcribe-metadata pipeline with prompt field."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "transcribe-image-metadata",
            "type": "transcribe-metadata",
            "model": "cosmos-reason2-8b",
            "customFunction": None,
            "eventFilter": {
                "objectSuffix": ["*.jpg", "*.png", "*.jpeg"],
                "maxObjectSize": "10737418240",
            },
            "schema": "default-transcribe-metadata-schema",
            "prompt": "Transcribe the image content into text.",
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.get_pipeline(name="transcribe-image-metadata")

    assert isinstance(result, V1PipelineResponse)
    assert result.name == "transcribe-image-metadata"
    assert result.type == "transcribe-metadata"
    assert result.model == "cosmos-reason2-8b"
    assert result.schema_name == "default-transcribe-metadata-schema"
    assert result.prompt == "Transcribe the image content into text."
    assert result.eventFilter["objectSuffix"] == ["*.jpg", "*.png", "*.jpeg"]


def test_get_pipeline_unauthorized(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        pipeline_api.get_pipeline(name="Test Pipeline")


def test_get_pipeline_unexpected_status(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        pipeline_api.get_pipeline(name="Test Pipeline")


def test_get_pipelines_success(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json=[
            {"id": "1", "name": "pipeline1"},
            {"id": "2", "name": "pipeline2"},
            {"id": "3", "name": "pipeline3"},
        ],
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.get_pipelines()

    assert isinstance(result, ListPipelines)
    assert len(result.root) == 3
    assert result.root[0].name == "pipeline1"
    assert result.root[0].id == "1"
    assert result.root[1].name == "pipeline2"
    assert result.root[2].name == "pipeline3"


def test_get_pipelines_unauthorized(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        pipeline_api.get_pipelines()


def test_delete_pipeline_success(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "status": "succesfully deleted pipeline",
            "Error": {"message": "Pipeline deleted successfully", "success": True},
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.delete_pipeline(name="Test Pipeline")

    assert isinstance(result, V1DeletePipelineResponse)
    assert result.status == "succesfully deleted pipeline"
    assert result.Error["message"] == "Pipeline deleted successfully"
    assert result.Error["success"] is True


def test_delete_pipeline_unauthorized(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.UNAUTHORIZED)
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        pipeline_api.delete_pipeline(name="Test Pipeline")


def test_delete_pipeline_unexpected_status(mocker, mock_session, pipeline_api):
    mock_response = HTTPXResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        pipeline_api.delete_pipeline(name="Test Pipeline")
