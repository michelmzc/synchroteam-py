from typing import Optional

from .base_api import BaseAPI

class CustomersAPI(BaseAPI):
    MISSING_IDENTIFIER_ERROR = "At least one of id, my_id or num is required to get a customer"

    def __init__(self, client: "SynchroteamClient"): # type: ignore
        super().__init__(client)

    def get(
            self, 
            id: Optional[str]=None,                       
            num: Optional[int]=None,
            my_id: Optional[str]=None
        ):
        """
            Get a customeer by identifier.
            
            Priority order:
                1. id: internal synchroteam id
                2. num: synchroteam number
                3. my_id: custom id

            If more than one identifier is provided, only the
            highest-priority identifier will be used.
        """
        
        endpoint = "/customer/details"
        params = self._get_identifier_params(
            identifier_error=self.MISSING_IDENTIFIER_ERROR,
            id=id,
            num=num,
            my_id=my_id
        )
        
        return self.client._request("GET", endpoint, params=params)