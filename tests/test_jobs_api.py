
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

# Ajusta estas importaciones a la estructura de tu proyecto.
from synchroteam_py.endpoints.jobs.jobs_api import JobsAPI
import synchroteam_py.endpoints.jobs.jobs_api as jobs_module


@pytest.fixture
def client():
    mock = Mock()
    mock.base_url = "https://example.com/api"
    mock.headers = {"Authorization": "test"}
    return mock


@pytest.fixture
def jobs_api(client, monkeypatch):
    # Evita inicializar dependencias reales de ReportAPI.
    monkeypatch.setattr(jobs_module, "ReportAPI", Mock())
    return JobsAPI(client, report=Mock())


# --------------------------------------------------
# check_status_job
# --------------------------------------------------

def test_check_status_job_filters_matching_status(jobs_api):
    job_list = [
        {"id": "1", "status": "completed"},
        {"id": "2", "status": "created"},
        {"id": "3", "status": "completed"},
    ]

    result = jobs_api.check_status_job(job_list, "completed")

    assert result == [
        {"id": "1", "status": "completed"},
        {"id": "3", "status": "completed"},
    ]


def test_check_status_job_returns_empty_list(jobs_api):
    assert jobs_api.check_status_job([], "completed") == []


def test_check_status_job_without_matches(jobs_api):
    result = jobs_api.check_status_job(
        [{"id": "1", "status": "created"}],
        "completed",
    )

    assert result == []


# --------------------------------------------------
# get_job_types / get_jobs / get_all_jobs
# --------------------------------------------------

def test_get_job_types(jobs_api, client):
    client._request.return_value = [{"id": 1}]

    result = jobs_api.get_job_types()

    assert result == [{"id": 1}]
    client._request.assert_called_once_with(
        "GET", "/jobtype/list"
    )


def test_get_jobs(jobs_api, client):
    params = {"status": "completed"}
    client._request.return_value = [{"id": "123"}]

    result = jobs_api.get_jobs(params=params)

    assert result == [{"id": "123"}]
    client._request.assert_called_once_with(
        "GET", "/job/list", params=params
    )


def test_get_all_jobs(jobs_api, client):
    client.get_all_records.return_value = [{"id": "123"}]
    params = {"status": "completed"}

    result = jobs_api.get_all_jobs(extra_params=params)

    assert result == [{"id": "123"}]
    client.get_all_records.assert_called_once_with(
        url=f"{client.base_url}/job/list",
        headers=client.headers,
        extra_params=params,
    )


# --------------------------------------------------
# Identificadores y get_job_by_id
# --------------------------------------------------

def test_get_job_by_id_uses_id_priority(jobs_api, client):
    jobs_api.get_job_by_id(id="123", num=10, my_id="abc")

    client._request.assert_called_once_with(
        "GET", "/job/details", params={"id": "123"}
    )


def test_get_job_by_id_uses_num_when_id_absent(
    jobs_api, client
):
    jobs_api.get_job_by_id(num=10, my_id="abc")

    client._request.assert_called_once_with(
        "GET", "/job/details", params={"num": 10}
    )


def test_get_job_by_id_uses_my_id_as_fallback(
    jobs_api, client
):
    jobs_api.get_job_by_id(my_id="abc")

    client._request.assert_called_once_with(
        "GET", "/job/details", params={"myId": "abc"}
    )


def test_get_job_by_id_without_identifier_raises(
    jobs_api, client
):
    with pytest.raises(ValueError, match="Must provide"):
        jobs_api.get_job_by_id()

    client._request.assert_not_called()


# --------------------------------------------------
# get_jobs_by_time_between
# --------------------------------------------------

def test_get_jobs_by_time_between(jobs_api, monkeypatch):
    expected = [{"id": "1"}]
    get_all_jobs = Mock(return_value=expected)
    monkeypatch.setattr(jobs_api, "get_all_jobs", get_all_jobs)

    result = jobs_api.get_jobs_by_time_between(
        "2026-01-01",
        "2026-01-31",
        extra_params={"status": "completed"},
    )

    assert result == expected
    get_all_jobs.assert_called_once_with(
        extra_params={
            "dateFrom": "2026-01-01",
            "dateTo": "2026-01-31",
            "status": "completed",
        }
    )


def test_get_jobs_by_time_between_without_extra_params(
    jobs_api, monkeypatch
):
    get_all_jobs = Mock(return_value=[])
    monkeypatch.setattr(jobs_api, "get_all_jobs", get_all_jobs)

    jobs_api.get_jobs_by_time_between(
        "2026-01-01", "2026-01-31"
    )

    get_all_jobs.assert_called_once_with(
        extra_params={
            "dateFrom": "2026-01-01",
            "dateTo": "2026-01-31",
        }
    )


# --------------------------------------------------
# target_photo_filter
# --------------------------------------------------

def test_target_photo_filter_returns_matching_photos(jobs_api):
    photos = {
        "jobPhoto": [
            {"id": "1", "comment": "before"},
            {"id": "2", "comment": "after"},
            {"id": "3", "comment": "before"},
        ]
    }

    result = jobs_api.target_photo_filter(
        photos, ["before"]
    )

    assert result == [
        {"id": "1", "comment": "before"},
        {"id": "3", "comment": "before"},
    ]


def test_target_photo_filter_returns_none_without_matches(
    jobs_api,
):
    result = jobs_api.target_photo_filter(
        {"jobPhoto": [{"comment": "other"}]},
        ["before"],
    )

    assert result is None


def test_target_photo_filter_with_empty_photos(jobs_api):
    assert jobs_api.target_photo_filter(
        {"jobPhoto": []}, ["before"]
    ) is None


# --------------------------------------------------
# get_photos
# --------------------------------------------------

def test_get_photos_returns_all_photos(jobs_api, client):
    response = {"jobPhoto": [{"id": "1", "comment": "before"}]}
    client._request.return_value = response

    result = jobs_api.get_photos(id="123")

    assert result == response
    client._request.assert_called_once_with(
        "GET", "/job/photos", params={"id": "123"}
    )


def test_get_photos_filters_target_photos(jobs_api, client):
    client._request.return_value = {
        "jobPhoto": [
            {"id": "1", "comment": "before"},
            {"id": "2", "comment": "after"},
        ]
    }

    result = jobs_api.get_photos(
        id="123", target_photos=["after"]
    )

    assert result == [{"id": "2", "comment": "after"}]


def test_get_photos_returns_not_found_message(
    jobs_api, client
):
    client._request.return_value = {
        "jobPhoto": [{"id": "1", "comment": "before"}]
    }

    result = jobs_api.get_photos(
        id="123", target_photos=["missing"]
    )

    assert result == "Photo not found"


def test_get_photos_without_identifier_raises(
    jobs_api, client
):
    with pytest.raises(ValueError, match="Must provide"):
        jobs_api.get_photos()

    client._request.assert_not_called()


# --------------------------------------------------
# Download methods
# --------------------------------------------------

def test_download_single_photo(jobs_api, monkeypatch):
    download = Mock(return_value="downloaded.jpg")
    monkeypatch.setattr(
        jobs_module, "download_single_photo", download
    )

    result = jobs_api.download_single_photo(
        {"id": "1"}, "/tmp", "photo.jpg"
    )

    assert result == "downloaded.jpg"
    download.assert_called_once_with(
        {"id": "1"}, "/tmp", "photo.jpg"
    )


def test_download_job_photos(jobs_api, monkeypatch):
    photos = [{"id": "1"}]
    get_photos = Mock(return_value=photos)
    monkeypatch.setattr(jobs_api, "get_photos", get_photos)

    download = Mock(return_value=["photo.jpg"])
    monkeypatch.setattr(
        jobs_module, "download_job_photos", download
    )

    result = jobs_api.download_job_photos(
        id="123", num=None, folder_route="/tmp/photos"
    )

    assert result == ["photo.jpg"]
    get_photos.assert_called_once_with(id="123", num=None)
    download.assert_called_once_with(
        photos=photos,
        folder_route="/tmp/photos",
        max_workers=5,
    )


# --------------------------------------------------
# get_jobs_by_last_hour_modified
# --------------------------------------------------

def test_get_jobs_by_last_hour_modified(jobs_api, client):
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(minutes=5)).isoformat().replace(
        "+00:00", "Z"
    )
    old = (now - timedelta(hours=2)).isoformat().replace(
        "+00:00", "Z"
    )

    jobs = [
        {"id": "old", "dateModified": old},
        {"id": "recent", "dateModified": recent},
        {"id": "missing"},
    ]

    client.parse_utc.side_effect = lambda value: (
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    )

    result = jobs_api.get_jobs_by_last_hour_modified(jobs)

    assert [job["id"] for job in result] == ["recent"]


def test_get_jobs_by_last_hour_modified_empty_list(
    jobs_api, client
):
    assert jobs_api.get_jobs_by_last_hour_modified([]) == []
    client.parse_utc.assert_not_called()


# --------------------------------------------------
# delete
# --------------------------------------------------

def test_delete_by_id(jobs_api, client):
    client._request.return_value = {"success": True}

    result = jobs_api.delete(id="123")

    assert result == {"success": True}
    client._request.assert_called_once_with(
        method="DELETE",
        endpoint="/job/delete",
        params={"id": "123"},
    )


def test_delete_without_identifier_raises(
    jobs_api, client
):
    with pytest.raises(ValueError, match="Must provide"):
        jobs_api.delete()

    client._request.assert_not_called()
