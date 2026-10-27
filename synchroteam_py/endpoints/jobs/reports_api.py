import logging
import requests
from typing import Dict, Optional, Any

from ..base_api import BaseAPI

logger = logging.getLogger(__name__)

class ReportAPI(BaseAPI):
    MISSING_IDENTIFIER = "Must provide a id, num or my_id for a valid Job"

    def __init__(self, client: "SynchroteamClient"): # type: ignore
        super().__init__(client)

    def get_job_report(
            self, 
            id: Optional[str] = None, 
            num: Optional[int] = None, 
            my_id: Optional[str] = None
        ) -> Optional[Dict[str, Any]]:
        """ Get job report by id, num or myId """ 
        
        endpoint = "/jobReport/details"        

        params = self._get_identifier_params(id=id, num=num, my_id=my_id, identifier_error=self.MISSING_IDENTIFIER)        
        
        try:
            job_report = self.client._request("GET", endpoint, params=params)        
            return job_report
        
        except requests.exceptions.HTTPError as error:
            response = error.response
            
            if response is not None:
                if response.status_code == 404:
                    logger.warning("Job report not found: endpoint=%s params=%s", endpoint, params)
                    return None
                
                logger.error("HTTP error getting job report: status=%s endpoint=%s", response.status_code, endpoint)
                return None

            logger.exception("HTTP error without response getting job report: %s", error)
            return None

        except requests.exceptions.RequestException as error:
            logger.exception("Error getting the job report: %s", error)
            return None

    
    def get_report_item(self, report: Dict, item_name: str) -> Optional[dict]:
        """ Get a report Dict and get a item by it's name """
        
        for item in report["items"]:
            if item.get("name") == item_name:
                return item
        
        return None