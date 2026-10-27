import pytest
from unittest.mock import Mock

from synchroteam_py.endpoints.customers_api import CustomersAPI


@pytest.fixture
def client():
    return Mock()


@pytest.fixture
def customers_api(client):
    return CustomersAPI(client)


def test_get_by_id(customers_api, client):
    expected = {"id": "123", "name": "Customer"}

    client._request.return_value = expected

    result = customers_api.get(id="123")

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/customer/details",
        params={"id": "123"},
    )


def test_get_by_my_id(customers_api, client):
    expected = {"id": "123", "name": "Customer"}

    client._request.return_value = expected

    result = customers_api.get(my_id="CUST001")

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/customer/details",
        params={"myId": "CUST001"},
    )


def test_get_by_num(customers_api, client):
    expected = {"id": "123", "name": "Customer"}

    client._request.return_value = expected

    result = customers_api.get(num="100")

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/customer/details",
        params={"num": "100"},
    )


def test_get_requires_identifier(customers_api):
    with pytest.raises(
        ValueError,
        match="At least one of id, myId or num is required"
    ):
        customers_api.get()


def test_get_prioritizes_id_over_other_identifiers(
    customers_api,
    client
):
    expected = {"id": "123"}

    client._request.return_value = expected

    result = customers_api.get(
        id="123",
        my_id="CUST001",
        num="100",
    )

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/customer/details",
        params={"id": "123"},
    )

def test_get_equipment_prioritizes_id(equipment_api, client):
    expected = {"id": "123"}

    client._request.return_value = expected

    result = equipment_api.get(
        id="123",
        my_id="EQ001",
        num=100,
    )

    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/equipment/details",
        params={"id": "123"},
    )

def test_get_equipment_prioritizes_my_id_over_num(equipment_api, client):
    expected = {"id": "123"}
    
    client._request.return_value = expected
    
    result = equipment_api.get(
        my_id="EQ001",
        num=100,
    )
    
    assert result == expected

    client._request.assert_called_once_with(
        "GET",
        "/equipment/details",
        params={"myId": "EQ001"},
    )