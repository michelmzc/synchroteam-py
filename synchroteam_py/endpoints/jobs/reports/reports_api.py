import logging
import requests
from typing import Dict, Optional


logger = logging.getLogger(__name__)
class ReportAPI:
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client


    def get_job_report(
            self, 
            id: Optional[str] = None, 
            num: Optional[str] = None, 
            my_id: Optional[str] = None
        ):
        """ Get job report by id, num or myId """ 
        
        endpoint = "/jobReport/details"        
        params = {}
        
        if id is not None:
            params["id"] = id
        elif num is not None:
            params["num"] = num
        elif my_id is not None:
            params["myId"] = my_id
        else:
            raise ValueError("Must provide a id, num or myId")
        
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

            logger.exception("HTTP error wothout response getting job report: %s", error)

        except requests.exceptions.RequestException as error:
            logger.exception("Error getting the job report: %s", error)
            return None

    
    def get_report_item(self, report: Dict, item_name: str) -> Optional[dict]:
        """ Get a report Dict and get a item by it's name """
        
        for item in report["items"]:
            if item.get("name") == item_name:
                return item
        return None
        
