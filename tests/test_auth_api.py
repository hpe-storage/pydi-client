# Copyright Hewlett Packard Enterprise Development LP

import pytest
from pydi_client.api.auth import AuthAPI
from pydi_client.sessions.authenticated_session import AuthenticatedSession
from pydi_client.errors import NotImplementedException
import httpx


@pytest.fixture
def mock_httpx_client(mocker):
    # Mock the httpx client returned by Session
    mock_client = mocker.MagicMock()
    mocker.patch(
        "pydi_client.sessions.session.Session.get_httpx_client",
        return_value=mock_client,
    )
    return mock_client


def test_login_success(mock_httpx_client):
    # Mock response for successful login
    mock_response = mock_httpx_client.request.return_value
    mock_response.status_code = httpx.codes.OK

    sample_token = "mock_token"
    mock_response.json.return_value = {
        "Status": "Login successful",
        "Authorization": f"Bearer {sample_token}",
    }

    # Call the login method
    session = AuthAPI.login(uri="http://example.com", username="user", password="pass")

    # Assertions
    assert isinstance(session, AuthenticatedSession)
    assert session.token == "Bearer mock_token"
    assert session.username == "user"
    assert session.password == "pass"


def test_login_failure_status_code(mock_httpx_client):
    # Mock response for failed login
    mock_response = mock_httpx_client.request.return_value
    mock_response.status_code = httpx.codes.UNAUTHORIZED

    # Call the login method and expect an exception
    with pytest.raises(
        httpx.HTTPStatusError, match="Login failed with status code 401"
    ):
        AuthAPI.login(uri="http://example.com", username="user", password="pass")


def test_login_failure_no_token(mock_httpx_client):
    # Mock response with no token in the response
    mock_response = mock_httpx_client.request.return_value
    mock_response.status_code = httpx.codes.OK
    mock_response.json.return_value = {}

    # Call the login method and expect an exception
    with pytest.raises(
        httpx.HTTPStatusError, match="Login failed, no JWT token in response"
    ):
        AuthAPI.login(uri="http://example.com", username="user", password="pass")


def test_refresh(mock_httpx_client):
    # Mock response for successful login
    mock_response = mock_httpx_client.request.return_value
    mock_response.status_code = httpx.codes.OK

    sample_token = "mock_token"
    mock_response.json.return_value = {
        "Status": "Login successful",
        "Authorization": f"Bearer {sample_token}",
    }

    # Create a mock authenticated session
    session = AuthenticatedSession(
        uri="http://example.com", token="old_token", username="user", password="pass"
    )

    # Call the refresh method
    AuthAPI.refresh(session=session)

    # Assertions
    assert session.token == "Bearer mock_token"
    assert session.username == "user"
    assert session.password == "pass"
    assert session.uri == "http://example.com"


def test_logout():
    # Create a mock authenticated session
    session = AuthenticatedSession(
        uri="http://example.com", token="mock_token", username="user", password="pass"
    )

    # Call the logout method and expect a NotImplementedException
    with pytest.raises(NotImplementedException, match="Logout not implemented"):
        AuthAPI.logout(session=session)
