"""
client.py solo maneja requests (GET, POST, ...) y respuestas
"""
import time
import requests
import base64
from .config import DOMAIN, API_URL, API_KEY, USER, PASSWORD, WEB_URL
from typing import Dict, Optional, Any
from .utils import get_all_records, parse_utc
from pathlib import Path
from .endpoints.jobs.jobs_api import JobsAPI
from .endpoints.jobs.reports.reports_api import ReportAPI
from .endpoints.users import UsersAPI
from .endpoints.equipment import EquipmentAPI
from .endpoints.customers_api import CustomersAPI

class SynchroteamClient:
    def __init__(self):
        auth_string = f"{DOMAIN}:{API_KEY}"
        encoded_auth_string = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        self.base_url = API_URL
        self.web_url = WEB_URL
        self.user = USER
        self.password = PASSWORD
        self.cookies_file = "session.cookies"
        self.route = Path.cwd()
        #print(f"route: {self.route}")
        #print(f"Type: {type(self.route)}")
    
        self.headers = {
            "Authorization":f"Basic {encoded_auth_string}",
            "Content-Type":"application/json",
            "Accept":"text/json",
            "Cache-Control":"no-cache"
        }

        # creamos sesión que guardara cookies
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # Instancia de submódulos
        self.reports = ReportAPI(self)
        self.jobs = JobsAPI(self, report=self.reports)
        self.users = UsersAPI(self)
        self.equipment = EquipmentAPI(self)
        self.customers = CustomersAPI(self)

        
    # función núcleo de peticiones HTTP
    # puede que sea necesario agregar método de modificacón de las cabezera
    def _request(self, 
                 method:   str, 
                 endpoint: str, 
                 headers:  Optional[Dict] = None,
                 data:     Optional[Dict] = None, 
                 params:   Optional[Dict] = None,
        ) -> Any:
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        print(f"[{method.upper()}] request to: {url}")
        
        if headers:
            self.headers.update(headers)
            
        start_time = time.time()

        response = self.session.request(
            method = method.upper(),
            url = url,
            headers = self.headers, 
            json = data, 
            params = params
        )

        duration = time.time() - start_time
        #print(f"Request compeleted in {duration:.2f} seconds")

        # lanza excepción si la respuesta fue mala (4xx o 5xx)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print("HTTP Error:", e)
            print("Response Text:", response.text)
            raise
    
        # revisamos headers 
        
        #print("Response Headers:")
        for key, value in response.headers.items():
            if key == "X-Quota-Remaining":
                print(f"{key}:{value}")
            #print(keyvalue)
        
        return response.json()

    def test_connection(self) -> Any:
        """
        Realiza una petición básica para verificar autenticación y conectividad con la API.
        """
        return self._request("GET", "/job/list")