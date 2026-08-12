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
from pydi_client.errors import (
    HTTPUnauthorizedException,
    PipelineValidationError,
    UnexpectedStatus,
)
from pydi_client.di_client import DIAdminClient
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


def test_create_pipeline_preserves_serialized_payload(
    mocker, mock_session, pipeline_api
):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={"success": True, "message": "Pipeline created successfully"},
    )
    execute_request = mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    pipeline_api.create_pipeline(
        name="Test Pipeline",
        pipeline_type="type1",
        model="model1",
        custom_func="func1",
        event_filter_object_suffix=[".txt"],
        event_filter_max_object_size=100,
        schema="schema1",
    )

    assert execute_request.call_args.kwargs["json"] == {
        "name": "Test Pipeline",
        "type": "type1",
        "model": "model1",
        "eventFilter": {"objectSuffix": [".txt"], "maxObjectSize": 100},
        "schema": "schema1",
        "customFunction": "func1",
    }


@pytest.mark.parametrize(
    "field",
    ["name", "pipeline_type", "event_filter_object_suffix", "schema"],
)
def test_create_pipeline_missing_required_input_raises_client_validation_error(
    mocker, mock_session, pipeline_api, field
):
    execute_request = mocker.patch("pydi_client.api.pipeline.execute_with_retry")
    arguments = {
        "name": "Test Pipeline",
        "pipeline_type": "type1",
        "event_filter_object_suffix": [".txt"],
        "schema": "schema1",
    }
    arguments.pop(field)

    with pytest.raises(PipelineValidationError) as exception:
        pipeline_api.create_pipeline(**arguments)

    assert exception.value.source == "client"
    assert exception.value.status_code is None
    assert exception.value.errors == [
        {"type": "missing", "loc": [field], "msg": "Field required"}
    ]
    assert str(exception.value) == (
        f"Pipeline validation failed (client): {field}: Field required"
    )
    execute_request.assert_not_called()


def test_create_pipeline_schema_none_raises_client_validation_error(
    mocker, mock_session, pipeline_api
):
    execute_request = mocker.patch("pydi_client.api.pipeline.execute_with_retry")

    with pytest.raises(PipelineValidationError) as exception:
        pipeline_api.create_pipeline(
            name="Test Pipeline",
            pipeline_type="type1",
            event_filter_object_suffix=[".txt"],
            schema=None,
        )

    assert exception.value.source == "client"
    assert "schema: Input should be a valid string" in str(exception.value)
    execute_request.assert_not_called()


def test_admin_client_missing_pipeline_type_raises_client_validation_error(
    mocker, mock_session
):
    mocker.patch("pydi_client.di_client.AuthAPI.login", return_value=mock_session)
    execute_request = mocker.patch("pydi_client.api.pipeline.execute_with_retry")
    client = DIAdminClient(
        uri="http://example.com", username="admin", password="password"
    )

    with pytest.raises(PipelineValidationError):
        client.create_pipeline(
            name="Test Pipeline",
            event_filter_object_suffix=[".txt"],
            schema="schema1",
        )

    execute_request.assert_not_called()


def test_create_pipeline_gateway_validation_error(mocker, mock_session, pipeline_api):
    response_content = (
        b'{"Status":"invalid payload","errors":[{"type":"missing",'
        b'"loc":["rag","eventFilter","maxObjectSize"],'
        b'"msg":"Field required"}]}'
    )
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content=response_content
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    with pytest.raises(PipelineValidationError) as exception:
        pipeline_api.create_pipeline(
            name="Test Pipeline",
            pipeline_type="rag",
            event_filter_object_suffix=["*.pdf"],
            schema="schema1",
        )

    assert exception.value.source == "server"
    assert exception.value.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert exception.value.errors[0]["loc"] == [
        "rag",
        "eventFilter",
        "maxObjectSize",
    ]
    assert exception.value.errors[0]["msg"] == "Field required"
    assert exception.value.raw_response == response_content
    assert str(exception.value) == (
        "Pipeline validation failed (server): "
        "rag.eventFilter.maxObjectSize: Field required"
    )


def test_create_pipeline_semantic_gateway_validation_error(
    mocker, mock_session, pipeline_api
):
    response_content = b'{"Status":"Invalid maxObjectSize","error":"limit exceeded"}'
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content=response_content
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    with pytest.raises(PipelineValidationError) as exception:
        pipeline_api.create_pipeline(
            name="Test Pipeline",
            pipeline_type="rag",
            event_filter_object_suffix=["*.pdf"],
            schema="schema1",
        )

    assert exception.value.source == "server"
    assert exception.value.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert exception.value.errors == [
        {
            "type": "server_validation_error",
            "loc": [],
            "msg": "limit exceeded",
            "status": "Invalid maxObjectSize",
        }
    ]
    assert exception.value.raw_response == response_content
    assert str(exception.value) == (
        "Pipeline validation failed (server): Invalid maxObjectSize: limit exceeded"
    )


@pytest.mark.parametrize("response_content", [b"not json", b"\xff"])
def test_create_pipeline_nonstandard_gateway_validation_error(
    mocker, mock_session, pipeline_api, response_content
):
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY, content=response_content
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    with pytest.raises(PipelineValidationError) as exception:
        pipeline_api.create_pipeline(
            name="Test Pipeline",
            pipeline_type="type1",
            event_filter_object_suffix=[".txt"],
            schema="schema1",
        )

    assert exception.value.source == "server"
    assert exception.value.errors == []
    assert exception.value.raw_response == response_content
    assert (
        str(exception.value) == "Pipeline validation failed (server): no error details"
    )


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


@pytest.mark.parametrize(
    "status_code",
    [HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.INTERNAL_SERVER_ERROR],
)
def test_create_pipeline_unexpected_status(
    mocker, mock_session, pipeline_api, status_code
):
    mock_response = HTTPXResponse(status_code=status_code)
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

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
        json={
            "success": True,
            "message": "transcribe-image-metadata resource created successfully.",
        },
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


def test_create_custom_function_pipeline_with_event_filter_success(
    mocker, mock_session, pipeline_api
):
    """Test creating a custom-function pipeline with explicit eventFilter."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "success": True,
            "message": "example-custom-function-pipeline resource created successfully.",
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.create_pipeline(
        name="example-custom-function-pipeline",
        pipeline_type="custom-function",
        model="di-custom-function-model",
        schema="yolo-detection-schema",
        event_filter_object_suffix=["*.jpeg", "*.jpg", "*.png"],
        event_filter_max_object_size=10485760,
    )

    assert isinstance(result, V1CreatePipelineResponse)
    assert result.success is True
    assert "example-custom-function-pipeline" in result.message


def test_get_custom_function_pipeline_success(mocker, mock_session, pipeline_api):
    """Test retrieving a custom-function pipeline."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "example-custom-function-pipeline",
            "type": "custom-function",
            "model": "di-custom-function-model",
            "customFunction": None,
            "eventFilter": {
                "objectSuffix": ["*.jpeg", "*.jpg", "*.png"],
                "maxObjectSize": 10485760,
            },
            "schema": "yolo-detection-schema",
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.get_pipeline(name="example-custom-function-pipeline")

    assert isinstance(result, V1PipelineResponse)
    assert result.name == "example-custom-function-pipeline"
    assert result.type == "custom-function"
    assert result.model == "di-custom-function-model"
    assert result.schema_name == "yolo-detection-schema"
    assert result.customFunction is None
    assert result.prompt is None
    assert result.eventFilter["objectSuffix"] == ["*.jpeg", "*.jpg", "*.png"]
    assert result.eventFilter["maxObjectSize"] == 10485760


def test_create_nim_rag_pipeline_success(mocker, mock_session, pipeline_api):
    """Test creating a NIM RAG pipeline with llama-nemotron-embed-1b-v2 model."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "success": True,
            "message": "nim-rag-pipeline resource created successfully.",
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.create_pipeline(
        name="nim-rag-pipeline",
        pipeline_type="rag",
        model="llama-nemotron-embed-1b-v2",
        schema="default-rag-schema",
        event_filter_object_suffix=[
            "*.pdf",
            "*.txt",
            "*.docx",
            "*.csv",
            "*.html",
            "*.json",
        ],
        event_filter_max_object_size=1000000,
        chunk_size=512,
        chunk_overlap=50,
    )

    assert isinstance(result, V1CreatePipelineResponse)
    assert result.success is True
    assert "nim-rag-pipeline" in result.message


def test_get_nim_rag_pipeline_success(mocker, mock_session, pipeline_api):
    """Test retrieving the NIM RAG pipeline."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "nim-rag-pipeline",
            "type": "rag",
            "model": "llama-nemotron-embed-1b-v2",
            "customFunction": None,
            "eventFilter": {
                "objectSuffix": [
                    "*.pdf",
                    "*.txt",
                    "*.docx",
                    "*.csv",
                    "*.html",
                    "*.json",
                ],
                "maxObjectSize": 1000000,
            },
            "schema": "default-rag-schema",
            "chunkSize": 512,
            "chunkOverlap": 50,
            "prompt": None,
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.get_pipeline(name="nim-rag-pipeline")

    assert isinstance(result, V1PipelineResponse)
    assert result.name == "nim-rag-pipeline"
    assert result.type == "rag"
    assert result.model == "llama-nemotron-embed-1b-v2"
    assert result.schema_name == "default-rag-schema"
    assert result.prompt is None
    assert result.eventFilter["objectSuffix"] == [
        "*.pdf",
        "*.txt",
        "*.docx",
        "*.csv",
        "*.html",
        "*.json",
    ]
    assert result.eventFilter["maxObjectSize"] == 1000000


def test_create_video_transcribe_pipeline_success(mocker, mock_session, pipeline_api):
    """Test creating a video transcribe-metadata pipeline."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "success": True,
            "message": "transcribe-video-metadata resource created successfully.",
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.create_pipeline(
        name="transcribe-video-metadata",
        pipeline_type="transcribe-metadata",
        model="parakeet-1_1b-rnnt-multilingual-asr",
        event_filter_object_suffix=["*.mp4"],
        event_filter_max_object_size=524288000,
        prompt="Transcribe the speech content into text.",
        schema="default-transcribe-metadata-schema",
    )

    assert isinstance(result, V1CreatePipelineResponse)
    assert result.success is True
    assert "transcribe-video-metadata" in result.message


def test_get_video_transcribe_pipeline_success(mocker, mock_session, pipeline_api):
    """Test retrieving the video transcribe-metadata pipeline."""
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "transcribe-video-metadata",
            "type": "transcribe-metadata",
            "model": "parakeet-1_1b-rnnt-multilingual-asr",
            "customFunction": None,
            "eventFilter": {
                "objectSuffix": ["*.mp4"],
                "maxObjectSize": 524288000,
            },
            "schema": "default-transcribe-metadata-schema",
            "prompt": "Transcribe the speech content into text.",
        },
    )
    mocker.patch(
        "pydi_client.api.pipeline.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_session.get_httpx_client.return_value = mock_httpx_client

    result = pipeline_api.get_pipeline(name="transcribe-video-metadata")

    assert isinstance(result, V1PipelineResponse)
    assert result.name == "transcribe-video-metadata"
    assert result.type == "transcribe-metadata"
    assert result.model == "parakeet-1_1b-rnnt-multilingual-asr"
    assert result.schema_name == "default-transcribe-metadata-schema"
    assert result.prompt == "Transcribe the speech content into text."
    assert result.eventFilter["objectSuffix"] == ["*.mp4"]
    assert result.eventFilter["maxObjectSize"] == 524288000
