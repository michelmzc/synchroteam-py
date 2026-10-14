import json
import logging
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch, ANY

import pytest
import requests

# Ajusta el import al nombre real de tu paquete
from synchroteam_py.client import SynchroteamClient


def make_response(
    payload: Any = None,
    status: int = 200,
    headers: Optional[Dict[str, str]] = None,
) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode() if payload is not None else b""
    response.headers.update(headers or {})
    return response


@pytest.fixture(name="client")
def client_fixture() -> SynchroteamClient:
    return SynchroteamClient(domain="domain", api_key="key")


def test_request_returns_json(client):
    client.session.request = MagicMock(return_value=make_response({"ok": True}))

    assert client._request("GET", "/job/list") == {"ok": True}


def test_request_empty_body_returns_none(client):
    client.session.request = MagicMock(return_value=make_response(status=204))

    assert client._request("DELETE", "/job/1") is None


def test_request_http_error_is_raised(client):
    client.session.request = MagicMock(return_value=make_response({}, status=500))

    with pytest.raises(requests.HTTPError):
        client._request("GET", "/job/list")


def test_low_quota_logs_warning(client):
    client.session.request = MagicMock(
        return_value=make_response({}, headers={"X-Quota-Remaining": "10"})
    )

    with patch("synchroteam_py.client.logger") as mock_logger:
        client._request("GET", "/job/list")

    mock_logger.warning.assert_called_once()
    assert "Low Synchroteam quota" in mock_logger.warning.call_args.args[0]


def test_invalid_quota_header_is_ignored(client):
    client.session.request = MagicMock(
        return_value=make_response({}, headers={"X-Quota-Remaining": "abc"})
    )

    with patch("synchroteam_py.client.logger") as mock_logger:
        result = client._request("GET", "/job/list")

    assert result == {}
    mock_logger.warning.assert_called_once()
    assert mock_logger.warning.call_args.args[1] == "X-Quota-Remaining"


def test_get_all_records_keeps_page_order(client):
    def fake_request(**kwargs):
        page = kwargs["params"]["page"]
        return make_response({"recordsTotal": 250, "data": [page]})

    client.session.request = MagicMock(side_effect=fake_request)

    assert client.get_all_records("/job/list", page_size=100) == [1, 2, 3]


def test_get_all_records_single_page(client):
    client.session.request = MagicMock(
        return_value=make_response({"recordsTotal": 2, "data": ["a", "b"]})
    )

    assert client.get_all_records("/job/list") == ["a", "b"]
    assert client.session.request.call_count == 1


def test_get_all_records_rejects_invalid_page_size(client):
    with pytest.raises(ValueError):
        client.get_all_records("/job/list", page_size=0)


def test_context_manager_closes_session():
    with SynchroteamClient(domain="demo", api_key="test-key") as client:
        client.session.close = MagicMock()

    client.session.close.assert_called_once()


def test_test_connection_calls_job_list(client):
    client.session.request = MagicMock(return_value=make_response({"data": []}))

    assert client.test_connection() == {"data": []}


def test_debug_headers_logs_response_headers(client):
    client.session.request = MagicMock(return_value=make_response({}))

    with patch("synchroteam_py.client.logger") as mock_logger:
        client._request("GET", "/job/list", debug_headers=True)

    mock_logger.debug.assert_any_call("Response headers: %s", ANY)

def test_high_quota_does_not_warn(client):
    client.session.request = MagicMock(
        return_value=make_response({}, headers={"X-Quota-Remaining": "10000"})
    )

    with patch("synchroteam_py.client.logger") as mock_logger:
        client._request("GET", "/job/list")

    mock_logger.warning.assert_not_called()