import pytest
from unittest.mock import Mock

from synchroteam_py.endpoints.base_api import BaseAPI


@pytest.fixture
def api():
    return BaseAPI(Mock())


def test_identifier_params_with_id(api):
    assert api._get_identifier_params(
        identifier_error="Missing identifier",
        id="123",
        num=45,
        my_id="abc",
    ) == {"id": "123"}


def test_identifier_params_with_num(api):
    assert api._get_identifier_params(
        identifier_error="Missing identifier",
        num=45,
        my_id="abc",
    ) == {"num": 45}


def test_identifier_params_with_my_id(api):
    assert api._get_identifier_params(
        identifier_error="Missing identifier",
        my_id="abc",
    ) == {"myId": "abc"}


def test_identifier_params_without_identifiers(api):
    with pytest.raises(
        ValueError,
        match="Missing identifier",
    ):
        api._get_identifier_params(
            identifier_error="Missing identifier",
        )