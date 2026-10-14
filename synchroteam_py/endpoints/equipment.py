from typing import Any

class EquipmentAPI:
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client

    def get_by_id(self, id: str) -> Any:
        if id is not None:
            endpoint = "/equipment/details"
            params = {
                "id": id
            }
            return self.client._request("GET", endpoint, params=params)
        else:
            return None
    def get_by_serial_number(self, serial_number: str) -> Any :
        if serial_number is not None:
            endpoint = "/equipment/details"
            params = {
                "myId": serial_number
            }
            return self.client._request("GET", endpoint, params=params)
        else:
            return None