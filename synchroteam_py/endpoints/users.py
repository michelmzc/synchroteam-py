from typing import Optional


class UsersAPI:
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client

    def get_all(self):
        """
            List of Synchroteam users
        """
        endpoint = "/user/list"

        return self.client.get_all_records(url=f"{self.client.base_url}{endpoint}", headers=self.client.headers) 

    def get_user_by_id(self, user_id: str = ""):
        """ Get a user by id """
        if (user_id != ""):
            endpoint = "/user/details"
            params = {
                "id": user_id
            }
            return self.client._request("GET", endpoint, params=params)
        else:
            None
            