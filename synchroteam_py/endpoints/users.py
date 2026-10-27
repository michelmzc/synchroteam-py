from typing import Optional

from .base_api import BaseAPI

class UsersAPI(BaseAPI):

    MISSING_IDENTIFIER_ERROR = "At least one of id, my_id or num is required to get a user"
    
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        super().__init__(client)

    def get_all(self):
        """
            List of Synchroteam users
        """
        endpoint = "/user/list"

        return self.client.get_all_records(endpoint=endpoint) 

    def get_by_id(
            self, 
            id: Optional[str]=None,                       
            num: Optional[int]=None,
            my_id: Optional[str]=None
        ):
        
        endpoint = "/user/details"
        
        params = self._get_identifier_params(
            identifier_error=self.MISSING_IDENTIFIER_ERROR,
            id=id,
            num=num,
            my_id=my_id
        )

        return self.client._request("GET", endpoint, params=params)