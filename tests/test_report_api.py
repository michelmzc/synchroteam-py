from unittest.mock import Mock

import pytest

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

    print(client._request.call_args)

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/jobReport/details",
        params={"id":"123"}
    )