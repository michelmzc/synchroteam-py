from typing import Any, Optional

from .base_api import BaseAPI

class EquipmentAPI(BaseAPI):
    
    MISSING_IDENTIFIER_ERROR = "At least one of id, my_id or num is required to get a equipment"
    
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client

    def get(self, 
            id: Optional[str]=None,                       
            num: Optional[int]=None,
            my_id: Optional[str]=None
        ) -> Any:        
        
        endpoint = "/equipment/details"
        params = self._get_identifier_params(
            identifier_error=self.MISSING_IDENTIFIER_ERROR,
            id=id,
            num=num,
            my_id=my_id
        )
        return self.client._request("GET", endpoint, params=params)