from typing import Any, Optional


class BaseAPI:
    def __init__(self, client: Any) -> None:
        self.client = client

    def _get_identifier_params(
        self,
        identifier_error: str,
        id: Optional[str] = None,
        num: Optional[int] = None,
        my_id: Optional[str] = None,
    ) -> dict:
        
        if id is not None:
            return {"id": id}
        if num is not None:
            return {"num": num}
        if my_id is not None:
            return {"myId": my_id}

        raise ValueError(identifier_error)