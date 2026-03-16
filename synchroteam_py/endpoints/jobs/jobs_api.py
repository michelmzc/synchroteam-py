"""
Usa client.py para obtener Trabajos, aplicar filtros, parseos, etc.
"""
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List

from .reports.reports_api import ReportAPI
from ._filters import check_status_job, get_jobs_by_last_hour_modified, target_photo_filter
from ._downloads import download_job_photos, download_single_photo, download_job_pdf, download_jobs_pdfs
from ...utils import get_all_records


class JobsAPI:
    def __init__(self, client: "SynchroteamClient", report: "ReportAPI"): # type: ignore
        self.client = client
        self.report =  ReportAPI(client)
    
    def get_job_types(self):
        """ Get the types of jobs defined in Synchroteam. """
        endpoint = f"/jobtype/list"        
        return self.client._request("GET", endpoint)

    
    def get_jobs(self, params: Optional[Dict] = None) -> List[Dict]:
        """ Get jobs based on custom parameters """
        endpoint = "/job/list"
        return self.client._request("GET", endpoint, params=params)
    
    def get_all_jobs(self, extra_params: Optional[Dict]) -> List[Dict]:
        """ Get jobs based on custom parameters using multithreading """
        return get_all_records(
            url = f"{self.client.base_url}/job/list",
            headers = self.client.headers,
            extra_params = extra_params
        )

    def get_job_by_id(self, id: Optional[str] = None, num: Optional[int] = None, myId: Optional[str] = None) -> Any:
        """ Get a job by id, num or myId """
        params = {}
        
        if id is not None:
            params["id"] = id
        elif num is not None:
            params["num"] = num
        elif myId is not None:
            params["myId"] = myId
        else:
            raise ValueError("Must provide a id, num or myId")
        
        return self.client._request("GET", "/job/details", params=params)
            

    def get_jobs_by_time_between(
            self,
            start_time: str, 
            end_time: str, 
            extra_params: Optional[Dict] = None
        ) -> List:
        """ Get jobs by start datetime and end datetime """
        params = {         
            "dateFrom": start_time,
            "dateTo":   end_time
        }

        if extra_params:
            params.update(extra_params)

        jobs = self.get_all_jobs(extra_params=params)

        return jobs  

    

    def get_photos(self, job_id: str = "", target_photo: str = "") -> Any:
        """ Get photos from a job by id """

        endpoint = f"/job/photos"        
        params = {"id":job_id}
        photos = self.client._request("GET", endpoint, params=params)

        if target_photo:
            photos = target_photo_filter(photos, target_photo)
            if photos: return photos
            else: return "Photo not found"

        return photos
    
    def download_single_photo(self, photo, folder):
        """ Download a single photo by photo id and folder destination """
        return download_single_photo(photo, folder)

    def download_job_photos(self, job_id, service_id, folder):
        """ Download job photos by job_id, myId and folder """
        photos = self.get_photos(job_id)
        return download_job_photos(photos, service_id, folder)


    def get_jobs_by_last_hour_modified(self, jobs):
        """ Filters a job list and order by last time modified """
        return get_jobs_by_last_hour_modified(jobs_list=jobs)
    

    def download_pdfs_from_services(self, job_id: str, service_id: str, folder="desktop"):
        """ Download pdf by myId to output folder and uses Selenium RPA """

        output_dir = Path(folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            download_job_pdf(job_id=job_id, service_id=service_id, folder=folder)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False