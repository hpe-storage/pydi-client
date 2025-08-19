# Copyright Hewlett Packard Enterprise Development LP

import pytest
from httpx import Response as HTTPXResponse
from http import HTTPStatus

from pydi_client.api.embedding_model import EmbeddingModelAPI

from pydi_client.data.model import (
    V1ModelsResponse,
    V1ListModelsResponse,
)

from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.errors import HTTPUnauthorizedException, UnexpectedStatus

from pydi_client.sessions.session import Session


@pytest.fixture
def mock_authsession(mocker):
    # Mock the AuthenticatedSession
    return mocker.MagicMock(spec=AuthenticatedSession)


@pytest.fixture
def mock_session(mocker):
    # Mock the regular Session
    return mocker.MagicMock(spec=Session)


@pytest.fixture
def embedding_model_api(mock_authsession):
    # Create an instance of EmbeddingModelAPI with the mocked session
    return EmbeddingModelAPI(session=mock_authsession)


def test_get_models_success(mocker, mock_authsession, embedding_model_api):
    # Mock the HTTP response
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK, json={"models": [
            {"id": "1", "name": "model1"}, {"id": "2", "name": "model2"}]}
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.embedding_model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    result = embedding_model_api.get_models()

    # Assertions
    assert isinstance(result, V1ListModelsResponse)
    assert len(result.models) == 2
    assert result.models[0].name == "model1"
    assert result.models[0].id == "1"
    assert result.models[1].name == "model2"
    assert result.models[1].id == "2"

    mock_execute_with_retry.assert_called_once()


def test_get_models_unauthorized(mocker, mock_authsession, embedding_model_api):
    # Mock the HTTP response for unauthorized access
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.UNAUTHORIZED,
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.embedding_model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        embedding_model_api.get_models()

    mock_execute_with_retry.assert_called_once()


def test_get_models_unexpected_status(mocker, mock_authsession, embedding_model_api):
    # Mock the HTTP response for an unexpected status
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.embedding_model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        embedding_model_api.get_models()

    mock_execute_with_retry.assert_called_once()


def test_get_model_success(mocker, mock_authsession, embedding_model_api):
    # Mock the HTTP response for a specific model
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "model1",
            "modelName": "text_embedding",
            "capabilities": ["embedding", "large language model"],
            "dimension": 768,
            "maximumTokens": 2048,
            "version": "1.0",
        },
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.embedding_model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    result = embedding_model_api.get_model(name="model1")

    # Assertions
    assert isinstance(result, V1ModelsResponse)
    assert result.name == "model1"
    assert result.modelName == "text_embedding"
    assert result.capabilities == ["embedding", "large language model"]
    assert result.dimension == 768
    assert result.maximumTokens == 2048
    assert result.version == "1.0"

    mock_execute_with_retry.assert_called_once()


def test_get_model_unauthorized(mocker, mock_authsession, embedding_model_api):
    # Mock the HTTP response for unauthorized access
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.UNAUTHORIZED,
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.embedding_model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        embedding_model_api.get_model(name="model1")

    mock_execute_with_retry.assert_called_once()


def test_get_model_unexpected_status(mocker, mock_authsession, embedding_model_api):
    # Mock the HTTP response for an unexpected status
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.embedding_model.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        embedding_model_api.get_model(name="model1")

    mock_execute_with_retry.assert_called_once()
