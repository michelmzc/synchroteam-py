"""
Clase relacionada a los clientes finales.
"""

from typing import Optional

class CustomersAPI:
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client
    
    def get_customer(self, customer_id: Optional[str]=None, 
                     customer_myId: Optional[str]=None, 
                     customer_num: Optional[str]=None
                     ):
        """
            Get a client by Synchroteam id, myId or num.
            Must be one parameters.
            Get by:
                id: internal synchroteam id
                myId: custom id
                num: synchroteam number

        """

        if not any([customer_id, customer_myId, customer_num]):
            raise ValueError("At least one of id, myId or num is required")

        endpoint = "/customer/details"
        params = {}

        if customer_id is not None:   params["id"]   = customer_id
        if customer_myId is not None: params["myId"] = customer_myId
        if customer_num is not None:  params["num"]  = customer_num
        
        return self.client._request("GET", endpoint, params=params)