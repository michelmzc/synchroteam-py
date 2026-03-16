import traceback
import requests
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class ReportAPI:
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client


    def get_job_report(self, id: Optional[str]=None, num:Optional[str]=None, myId: Optional[str]=None):
        """ Get job report by id, num or myId """ 
        endpoint = f"/jobReport/details"        

        params = {}
        
        if id is not None:
            params["id"] = id
        elif num is not None:
            params["num"] = num
        elif myId is not None:
            params["myId"] = myId
        else:
            raise ValueError("Must provide a id, num or myId")
        try:
            job_report = self.client._request("GET", endpoint, params=params)        
            return job_report
        except requests.exceptions.HTTPError as error:
            if error.response.status_code == 404:
                print(f"Report not found for job")
                return None
            else:
                print(f"Error HTTP {error.response.status_code}: {error}")
                return None
        except Exception as error:
            print(f"Error getting the report: {error}")
            return None

    
    def get_report_item(self, report: Dict, item_name: str) -> Any:
        """ Get a report Dict and get a item by it's name """
        item_found = None
        for item in report["items"]:
            if item.get("name") == item_name:
                item_found = item
                return item_found
        return None
        
