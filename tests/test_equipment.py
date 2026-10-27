import pytest

from unittest.mock import Mock

from synchroteam_py.endpoints.equipment_api import EquipmentAPI

@pytest.fixture
def client():
    return Mock()


@pytest.fixture
def equipment_api(client):
    return EquipmentAPI(client)


def test_get_equipment_by_id(equipment_api, client):
    expected = {"id": "123", "name": "Router"}

    client._request.return_value = expected

    result = equipment_api.get(id="123")

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/equipment/details",
        params={"id": "123"},
    )


def test_get_equipment_by_num(equipment_api, client):
    expected = {"id": "123", "name": "Router"}

    client._request.return_value = expected

    result = equipment_api.get(num=100)

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/equipment/details",
        params={"num": 100},
    )


def test_get_equipment_by_my_id(equipment_api, client):
    expected = {"id": "123", "name": "Router"}

    client._request.return_value = expected

    result = equipment_api.get(my_id="EQ001")

    assert result == expected

    # Probablemente _get_identifier_params convierte a myId
    client._request.assert_called_once_with(
        "GET",
        "/equipment/details",
        params={"myId": "EQ001"},
    )


def test_get_equipment_requires_identifier(equipment_api):
    with pytest.raises(
        ValueError,
        match=EquipmentAPI.MISSING_IDENTIFIER_ERROR
    ):
        equipment_api.get()