"""
Clase relacionada a los clientes finales.
"""

from typing import Optional

class CustomersAPI:
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client
    
    def get_customer(self, id: Optional[str]=None, 
                     my_id: Optional[str]=None, 
                     num: Optional[str]=None
                     ):
        """
            Get a client by Synchroteam id, myId or num.
            Must be one parameters.
            Get by:
                id: internal synchroteam id
                myId: custom id
                num: synchroteam number

        """

        if not any([id, my_id, num]):
            raise ValueError("At least one of id, myId or num is required")

        endpoint = "/customer/details"
        params = {}

        if id is not None:   params["id"]   = id
        if my_id is not None: params["myId"] = my_id
        if num is not None:  params["num"]  = num
        
        return self.client._request("GET", endpoint, params=params)