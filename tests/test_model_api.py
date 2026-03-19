# Copyright Hewlett Packard Enterprise Development LP

import pytest
from httpx import Response as HTTPXResponse
from http import HTTPStatus

from pydi_client.api.model import ModelAPI

from pydi_client.data.model import (
    V1ModelsResponse,
    V1ListModelsResponse,
    ModelTags
)

from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.errors import UnexpectedStatus, UnexpectedResponse

from pydi_client.sessions.session import Session
from pydi_client.di_client import DIAdminClient


@pytest.fixture
def mock_authsession(mocker):
    # Mock the AuthenticatedSession
    return mocker.MagicMock(spec=AuthenticatedSession)


@pytest.fixture
def mock_session(mocker):
    # Mock the regular Session
    return mocker.MagicMock(spec=Session)


@pytest.fixture
def model_api(mock_authsession):
    # Create an instance of ModelAPI with the mocked session
    return ModelAPI(session=mock_authsession)


def test_get_models_success(mocker, mock_authsession, model_api):
    # Mock the HTTP response
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK, json={"models": [
            {"id": "1", "name": "model1"}, {"id": "2", "name": "model2"}]}
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    result = model_api.get_models()

    # Assertions
    assert isinstance(result, V1ListModelsResponse)
    assert len(result.models) == 2
    assert result.models[0].name == "model1"
    assert result.models[0].id == "1"
    assert result.models[1].name == "model2"
    assert result.models[1].id == "2"

    mock_execute_with_retry.assert_called_once()

def test_get_all_embedding_models_success(mocker, mock_authsession):
    """
    Test that get_all_embedding_models filters models by Sentence-Similarity capability.
    The deprecated method on DIAdminClient calls get_models() to list all models,
    then get_model() for each to check capabilities, returning only embedding models.
    """
    # Mock AuthAPI.login to return the mock authenticated session
    mocker.patch(
        "pydi_client.di_client.AuthAPI.login", return_value=mock_authsession
    )

    # Create the admin client (login is mocked)
    client = DIAdminClient(uri="https://example.com", username="admin", password="password")

    # Mock get_models response (list of all models)
    mock_list_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={"models": [
            {"id": "1", "name": "embedding_model1"},
            {"id": "2", "name": "llm_model1"},
            {"id": "3", "name": "embedding_model2"},
        ]}
    )

    # Mock get_model responses per model name
    def model_detail_response(name):
        if name == "embedding_model1":
            return HTTPXResponse(
                status_code=HTTPStatus.OK,
                json={
                    "name": "embedding_model1",
                    "modelName": "text_embedding_1",
                    "capabilities": [ModelTags.SENTENCE_SIMILARITY.value],
                    "version": "1.0",
                    "communicationType": "Ollama API",
                    "dimension": 768,
                    "maximumTokens": 2048,
                    "contextLength": None,
                    "topK": None,
                    "topP": None,
                    "temperature": None,
                    "timeout": 30,
                    "language": None,
                    "sampleRate": None,
                    "automaticPunctuation": None,
                }
            )
        elif name == "llm_model1":
            return HTTPXResponse(
                status_code=HTTPStatus.OK,
                json={
                    "name": "llm_model1",
                    "modelName": "llama3",
                    "capabilities": ["Question-Answering"],
                    "version": "8b",
                    "communicationType": "Ollama API",
                    "dimension": None,
                    "maximumTokens": 1024,
                    "contextLength": 8000,
                    "topK": 40,
                    "topP": 0.9,
                    "temperature": 0.7,
                    "timeout": 120,
                    "language": None,
                    "sampleRate": None,
                    "automaticPunctuation": None,
                }
            )
        elif name == "embedding_model2":
            return HTTPXResponse(
                status_code=HTTPStatus.OK,
                json={
                    "name": "embedding_model2",
                    "modelName": "text_embedding_2",
                    "capabilities": [ModelTags.SENTENCE_SIMILARITY.value],
                    "version": "2.0",
                    "communicationType": "Ollama API",
                    "dimension": 1024,
                    "maximumTokens": 4096,
                    "contextLength": None,
                    "topK": None,
                    "topP": None,
                    "temperature": None,
                    "timeout": 60,
                    "language": None,
                    "sampleRate": None,
                    "automaticPunctuation": None,
                }
            )

    call_count = {"n": 0}

    def execute_with_retry_side_effect(session, request_func, **kwargs):
        url = kwargs.get("url", "")
        if url == "/api/v1/models":
            return mock_list_response
        # Individual model requests: /api/v1/models/<name>
        model_name = url.split("/api/v1/models/")[-1]
        return model_detail_response(model_name)

    mocker.patch(
        "pydi_client.api.model.execute_with_retry",
        side_effect=execute_with_retry_side_effect
    )

    mock_httpx_client = mocker.MagicMock()
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        result = client.get_all_embedding_models()

    # Assertions — only the two embedding models should be returned
    assert isinstance(result, V1ListModelsResponse)
    assert len(result.models) == 2
    assert result.models[0].name == "embedding_model1"
    assert result.models[0].id == "1"
    assert result.models[1].name == "embedding_model2"
    assert result.models[1].id == "3"


def test_get_models_unexpected_status(mocker, mock_authsession, model_api):
    # Mock the HTTP response for an unexpected status
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        model_api.get_models()

    mock_execute_with_retry.assert_called_once()


def test_get_model_success(mocker, mock_authsession, model_api):
    # Mock the HTTP response for a specific embedding model
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "model1",
            "modelName": "text_embedding",
            "capabilities": [ModelTags.SENTENCE_SIMILARITY.value],
            "version": "1.0",
            "communicationType": "Ollama API",
            "dimension": 768,
            "maximumTokens": 2048,
            "contextLength": None,
            "topK": None,
            "topP": None,
            "temperature": None,
            "timeout": 30,
            "language": None,
            "sampleRate": None,
            "automaticPunctuation": True
        }
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    result = model_api.get_model(name="model1")

    # Assertions
    assert isinstance(result, V1ModelsResponse)
    assert result.name == "model1"
    assert result.modelName == "text_embedding"
    assert result.capabilities == [ModelTags.SENTENCE_SIMILARITY.value]
    assert result.dimension == 768
    assert result.maximumTokens == 2048
    assert result.version == "1.0"
    assert result.communicationType == "Ollama API"
    assert result.timeout == 30
    assert result.automaticPunctuation is True

    mock_execute_with_retry.assert_called_once()

def test_get_model_unexpected_status(mocker, mock_authsession, model_api):
    # Mock the HTTP response for an unexpected status
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        model_api.get_model(name="model1")

    mock_execute_with_retry.assert_called_once()
