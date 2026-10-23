"""
Submodule of Jobs endpoint for SynchroteamClient
"""
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone, timedelta

# uses reports submodule
from .reports.reports_api import ReportAPI
from ..base_api import BaseAPI
from ._downloads import download_single_photo, download_job_photos

logger = logging.getLogger(__name__)
    
class JobsAPI(BaseAPI):
    MISSING_IDENTIFIER = "Must provide a id, num or my_id for a valid Job"

    def __init__(self, client: "SynchroteamClient", report: "ReportAPI"): # type: ignore
        self.client = client
        self.report =  ReportAPI(client) #Usualy a job involves a report 


    def check_status_job(self, job_list: List, status: str):
        """
        Check status jobs and returns as requested.
        Statuses: created, scheduled, synchronized, started, paused, completed, validated or cancelled        

        This function is a filter used when the status parameter included in get Jobs request doesn't work.
        """
        checked_jobs = []
        for job in job_list:
            job_status = job.get("status")
            if job_status == status:
                checked_jobs.append(job)
            
        return checked_jobs


    def get_job_types(self):
        """ Get the types of jobs defined in Synchroteam. """
        endpoint = "/jobtype/list"        
        return self.client._request("GET", endpoint)
    

    def get_jobs(self, params: Optional[Dict] = None) -> List[Dict]:
        """ Get jobs based on custom parameters """
        endpoint = "/job/list"
        return self.client._request("GET", endpoint, params=params)

    def get_all_jobs(self, extra_params: Optional[Dict]) -> List[Dict]:
        """ Get jobs based on custom parameters using multithreading """       
        return self.client.get_all_records(
            url = f"{self.client.base_url}/job/list",
            headers = self.client.headers,
            extra_params = extra_params
        )


    def get_job_by_id(self, id: Optional[str] = None, num: Optional[int] = None, my_id: Optional[str] = None) -> Any:
        """ Get a job by id, num or myId """
        params = self._get_identifier_params(identifier_error=self.MISSING_IDENTIFIER, id=id, num=num, my_id=my_id)
        
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


    def target_photo_filter(self, photos: Dict, target_photo: List):
        """ Get a photo by a filter they custom name"""
        targeted_photos = []

        for photo in photos["jobPhoto"]:
            if photo["comment"] in target_photo:
                targeted_photos.append(photo)
        
        if len(targeted_photos) <= 0:
            return None
        
        return targeted_photos
        

    def get_photos(self, id: Optional[str] = None, num: Optional[int] = None, my_id: Optional[str] = None, target_photos: List[str] = []) -> Any:
        """ Get photos from a job by id """
        endpoint = "/job/photos"        
        params = self._get_identifier_params(identifier_error=self.MISSING_IDENTIFIER, id=id, num=num, my_id=my_id)
        photos = self.client._request("GET", endpoint, params=params)

        if target_photos:
            photos = self.target_photo_filter(photos, target_photos)
            if photos: return photos
            else: return "Photo not found"
        return photos
    
    
    def download_single_photo(self, photo, folder, name):
        """ Download a single photo by photo id and folder destination """
        return download_single_photo(photo, folder, name)


    def download_job_photos(self, id, num, folder_route: str):
        """ Download job photos by job_id, myId and folder """
        photos = self.get_photos(id=id, num=num)
        return download_job_photos(photos=photos, folder_route=folder_route,max_workers=5)


    def get_jobs_by_last_hour_modified(self, jobs: List) -> List:
        """
        Get a job list and return a list order by last time modified
        """
        # get actual time
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)

        logger.debug("Filtering jobs modified between %s and %s", one_hour_ago, now)
            
        recent_jobs = []
        for job in jobs:
            date_modified = job.get("dateModified")
            if not date_modified:
                logger.warning("Job without dateModified field")
                continue

            modified_dt = self.client.parse_utc(date_modified)
                
            if modified_dt and one_hour_ago <= modified_dt <= now:
                logger.debug("Job modified within last hour: modified=%s", modified_dt)
                recent_jobs.append(job)
            
        # order by last time modified descendent (most recent first)
        recent_jobs.sort(key=lambda j: datetime.fromisoformat(j["dateModified"].rstrip('Z')), reverse=True)

        logger.info("Found %d jobs modified within the last hour", len(recent_jobs))

        return recent_jobs 
    
    def delete(self, id: Optional[str] = None, num: Optional[int] = None, my_id: Optional[str] = None) -> Any:

        params = self._get_identifier_params(identifier_error=self.MISSING_IDENTIFIER, id=id, num=num, my_id=my_id)
        
        endpoint = "/job/delete"

        return self.client._request(method="DELETE", endpoint=endpoint, params=params) 

        
