from typing import Optional
from ..utils import get_all_records

class UsersAPI:
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client

    def get_all(self):
        """
            Lista de usuarios de Synchroteam
        """
        endpoint = "/user/list"

        return get_all_records(url=f"{self.client.base_url}{endpoint}", headers=self.client.headers) 

    def get_user_by_id(self, user_id: str = ""):
        if (user_id != ""):
            endpoint = "/user/details"
            params = {
                "id": user_id
            }
            return self.client._request("GET", endpoint, params=params)
        else:
            None
    
    def get_customer(self, customer_id: Optional[str]=None, customer_myId: Optional[str]=None):
        """
            Busca un cliente por ID interno de Synchro (customer_id) o por ID externo (customer_myId).
            Debe enviarse al menos uno de los dos parámetros.
        """

        if not customer_id and not customer_myId:
            raise ValueError("Debe poporcionar 'customer_id' o 'customer_myId' para buscar un cliente.")

        endpoint = "/customer/details"
        params = {}

        # priorizar: si vienen ambos, customer_id manda
        if customer_id:
            params["id"] = customer_id
        elif customer_myId:
            params["myId"] = customer_myId
        
        return self.client._request("GET", endpoint, params=params)
    
    