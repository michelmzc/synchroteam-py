from unittest.mock import Mock

import pytest
import requests

from synchroteam_py.endpoints.jobs.reports_api import ReportAPI


@pytest.fixture
def client():
    return Mock()


@pytest.fixture
def report_api(client):
    return ReportAPI(client)


def test_get_job_report_by_id(report_api, client):
    expected = {"id": "123", "name": "Test"}

    client._request.return_value = expected

    result = report_api.get_job_report(id="123")

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/jobReport/details",
        params={"id": "123"},
    )


def test_get_job_report_by_num(report_api, client):
    expected = {"id": "123", "name": "Test"}

    client._request.return_value = expected

    result = report_api.get_job_report(num=100)

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/jobReport/details",
        params={"num": 100},
    )


def test_get_job_report_by_my_id(report_api, client):
    expected = {"id": "123", "name": "Test"}

    client._request.return_value = expected

    result = report_api.get_job_report(my_id="JOB001")

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/jobReport/details",
        params={"myId": "JOB001"},
    )


def test_get_job_report_returns_none_when_not_found(report_api, client):
    response = Mock()
    response.status_code = 404

    error = requests.exceptions.HTTPError(response=response)

    client._request.side_effect = error

    result = report_api.get_job_report(id="123")

    assert result is None


def test_get_job_report_returns_none_on_http_error(report_api, client):
    response = Mock()
    response.status_code = 500

    error = requests.exceptions.HTTPError(response=response)

    client._request.side_effect = error

    result = report_api.get_job_report(id="123")

    assert result is None


def test_get_job_report_returns_none_on_http_error_without_response(
    report_api, client
):
    error = requests.exceptions.HTTPError()

    client._request.side_effect = error

    result = report_api.get_job_report(id="123")

    assert result is None


def test_get_job_report_returns_none_on_request_exception(
    report_api, client
):
    client._request.side_effect = requests.exceptions.RequestException(
        "Connection error"
    )

    result = report_api.get_job_report(id="123")

    assert result is None


def test_get_job_report_requires_identifier(report_api):
    with pytest.raises(ValueError):
        report_api.get_job_report()


def test_get_report_item_found(report_api):
    report = {
        "items": [
            {"name": "status", "value": "open"},
            {"name": "customer", "value": "John"}
        ]
    }

    result = report_api.get_report_item(report, "customer")

    assert result == {
        "name": "customer",
        "value": "John"
    }


def test_get_report_item_not_found(report_api):
    report = {
        "items": [
            {"name": "status", "value": "open"}
        ]
    }

    result = report_api.get_report_item(report, "customer")

    assert result is None