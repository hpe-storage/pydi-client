# Copyright Hewlett Packard Enterprise Development LP

import pytest
from httpx import Response as HTTPXResponse
from http import HTTPStatus

from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.errors import HTTPUnauthorizedException, UnexpectedStatus

from pydi_client.sessions.session import Session

from pydi_client.api.schema import SchemaAPI
from pydi_client.data.schema import (
    V1SchemasResponse,
    V1ListSchemasResponse,
)


@pytest.fixture
def mock_authsession(mocker):
    # Mock the AuthenticatedSession
    return mocker.MagicMock(spec=AuthenticatedSession)


@pytest.fixture
def mock_session(mocker):
    # Mock the regular Session
    return mocker.MagicMock(spec=Session)


@pytest.fixture
def schema_api(mock_authsession):
    # Create an instance of SchemaAPI with the mocked session
    return SchemaAPI(session=mock_authsession)


def test_get_schemas_success(mocker, mock_authsession, schema_api):
    # Mock the HTTP response
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK, json={"schemas": [
            {"id": "1", "name": "schema1"}, {"id": "2", "name": "schema2"}]}
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.schema.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    result = schema_api.get_schemas()

    # Assertions
    assert isinstance(result, V1ListSchemasResponse)
    assert len(result.schemas) == 2
    assert result.schemas[0].name == "schema1"
    assert result.schemas[0].id == "1"
    assert result.schemas[1].name == "schema2"
    assert result.schemas[1].id == "2"

    mock_execute_with_retry.assert_called_once()


def test_get_schemas_unauthorized(mocker, mock_authsession, schema_api):
    # Mock the HTTP response for unauthorized access
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.UNAUTHORIZED, json={"detail": "Unauthorized"}
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.schema.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        schema_api.get_schemas()

    mock_execute_with_retry.assert_called_once()


def test_get_schemas_unexpected_status(mocker, mock_authsession, schema_api):
    # Mock the HTTP response for an unexpected status
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        json={"detail": "Internal Server Error"},
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.schema.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        schema_api.get_schemas()

    mock_execute_with_retry.assert_called_once()


def test_get_schema_success(mocker, mock_authsession, schema_api):
    # Mock the HTTP response
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.OK,
        json={
            "name": "schema1",
            "type": "metadata",
            "schema": [
                {"name": "object_key", "type": "varchar"},
                {"name": "bucket", "type": "varchar"},
                {"name": "version_id", "type": "varchar"},
                {"name": "size", "type": "bigint"},
                {"name": "last_modified", "type": "varchar"},
                {"name": "content_type", "type": "varchar"},
                {"name": "content_encoding", "type": "varchar"},
                {"name": "content_language", "type": "varchar"},
                {"name": "e_tag", "type": "varchar"},
                {"name": "user_metadata", "type": "map(varchar, varchar)"},
                {"name": "object_tags", "type": "map(varchar, varchar)"},
            ],
        },
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.schema.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    result = schema_api.get_schema(name="schema1")

    # Assertions
    assert isinstance(result, V1SchemasResponse)
    assert result.name == "schema1"
    assert result.type == "metadata"
    assert result.schema[0].name == "object_key"
    assert result.schema[0].type == "varchar"

    mock_execute_with_retry.assert_called_once()


def test_get_schema_unauthorized(mocker, mock_authsession, schema_api):
    # Mock the HTTP response for unauthorized access
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.UNAUTHORIZED, json={"detail": "Unauthorized"}
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.schema.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(HTTPUnauthorizedException):
        schema_api.get_schema(name="schema1")

    mock_execute_with_retry.assert_called_once()


def test_get_schema_unexpected_status(mocker, mock_authsession, schema_api):
    # Mock the HTTP response for an unexpected status
    mock_response = HTTPXResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        json={"detail": "Internal Server Error"},
    )

    mock_execute_with_retry = mocker.patch(
        "pydi_client.api.schema.execute_with_retry", return_value=mock_response
    )

    mock_httpx_client = mocker.MagicMock()
    mock_httpx_client.request.return_value = mock_response
    mock_authsession.get_httpx_client.return_value = mock_httpx_client

    with pytest.raises(UnexpectedStatus):
        schema_api.get_schema(name="schema1")

    mock_execute_with_retry.assert_called_once()
