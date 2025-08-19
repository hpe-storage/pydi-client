# Copyright Hewlett Packard Enterprise Development LP

import pytest
from unittest import mock
from pydi_client.sessions.session import Session


def test_session_initialization_defaults():
    s = Session(uri="http://example.com")
    assert s.uri == "http://example.com"
    assert s._headers == {}
    assert s._timeout == 300
    assert s._client is None
    assert s._httpx_args == {}


def test_session_initialization_custom():
    s = Session(uri="http://example.com", headers={"a": "b"}, timeout=10, httpx_args={"verify": True})
    assert s._headers == {"a": "b"}
    assert s._timeout == 10
    assert s._httpx_args == {"verify": True}


def test_with_headers_no_client():
    s = Session(uri="http://example.com", headers={"a": "b"})
    s2 = s.with_headers({"c": "d"})
    assert s2._headers == {"a": "b", "c": "d"}
    assert s._headers == {"a": "b"}


def test_with_headers_with_client():
    s = Session(uri="http://example.com", headers={"a": "b"})
    mock_client = mock.Mock()
    mock_client.headers = {"a": "b"}
    s._client = mock_client
    s2 = s.with_headers({"c": "d"})
    assert mock_client.headers["c"] == "d"
    assert s2._headers == {"a": "b", "c": "d"}


def test_with_timeout_no_client():
    s = Session(uri="http://example.com", timeout=10)
    s2 = s.with_timeout(20)
    assert s2._timeout == 20
    assert s._timeout == 10


def test_with_timeout_with_client():
    s = Session(uri="http://example.com", timeout=10)
    mock_client = mock.Mock()
    mock_client.timeout = 10
    s._client = mock_client
    s2 = s.with_timeout(20)
    assert mock_client.timeout == 20
    assert s2._timeout == 20


def test_set_httpx_client_sets_client_and_returns_self():
    s = Session(uri="http://example.com")
    mock_client = mock.Mock()
    result = s.set_httpx_client(mock_client)
    assert s._client is mock_client
    assert result is s


def test_get_httpx_client_creates_client(monkeypatch):
    s = Session(uri="http://example.com", headers={"x": "y"}, timeout=123, httpx_args={"foo": "bar"})
    mock_client_cls = mock.Mock()
    monkeypatch.setattr("httpx.Client", mock_client_cls)
    s._client = None
    client_instance = mock.Mock()
    mock_client_cls.return_value = client_instance
    result = s.get_httpx_client()
    mock_client_cls.assert_called_once_with(
        base_url="http://example.com",
        headers={"x": "y"},
        timeout=123,
        verify=False,
        foo="bar"
    )
    assert result is client_instance


def test_get_httpx_client_returns_existing_client():
    s = Session(uri="http://example.com")
    mock_client = mock.Mock()
    s._client = mock_client
    result = s.get_httpx_client()
    assert result is mock_client
