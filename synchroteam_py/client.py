"""
client.py solo maneja requests (GET, POST, ...) y respuestas
"""
import time
import requests
import base64

from typing import Dict, Optional, Any
from pathlib import Path
from math import ceil
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import Optional, Dict, List
from datetime import timezone
from dateutil.parser import parse 

from .config import DOMAIN, API_URL, API_KEY, USER, PASSWORD, WEB_URL
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
    # función para obtener todos los registros de una consulta desde su paginación
    def get_all_records(self, 
            url: str, 
            headers: Optional[Dict[str, str]], 
            extra_params: Optional[Dict] = None, 
            page_size: int = 100,         
            max_workers: int = 10
        ) -> List[Dict]:
        """
        Obtiene todos los registros desde una ruta dada, soporta paginación y threading.
        Filtra por type_name si se proporciona en extra_params.

        Argumentos: 
                url (str): URL de la ruta a pedir (sin parámetros).
                headers (dict): Parámetros para la cabecera de la solicitud.
                extra_params (dict): Parámetros adicionales para la consulta.
                page_size (int): Tamaño de registros por página (máximo API Synchroteam)
                max_workers (int): Número de hilos por concurrencia

        Retorna:
                list: Lista combinada con todos los registros filtrados
        """

        start_time = time.time()
        if extra_params is None:
            extra_params = {}
        
        initial_params = extra_params.copy()
        initial_params.update({
            "page": 1,
            "pageSize": page_size
        })

        response = requests.get(url, headers=headers, params=initial_params)
        response.raise_for_status()
        data = response.json()

        total_records = int(data.get("recordsTotal", 0))
        total_pages = ceil(total_records / page_size)
        
        print(f"Total records: { total_records } from { total_pages } pages per route: { url } and params: {initial_params}")

        records = data.get("data", [])

        def fetch_page(page: int):
            params = extra_params.copy()
            params.update({"page": page, "pageSize": page_size})
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json().get("data", [])
        
        # descargar en paralelo desde la página 2 hasta la última
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(fetch_page, page) 
                for page in range(2, total_pages + 1)
            ]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading records"):
                try: 
                    records.extend(future.result())
                except Exception as e:
                    print(f"Error fetching page: {e}")

        
        end_time = time.time()
        print(f"Records downloading completed in {end_time - start_time:.2f} seconds. "
            f"Total records: {len(records)}")
        
        return records
    
    # función que agrega timezone a un date string
    @staticmethod
    def parse_utc(dt_str):
        if not dt_str:
            return None 
        try:
            dt = parse(dt_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt 
        except Exception as e:
            print(f"Error parsing: {dt_str} -> {e}")
            return None

    def test_connection(self) -> Any:
        """
        Realiza una petición básica para verificar autenticación y conectividad con la API.
        """
        return self._request("GET", "/job/list")