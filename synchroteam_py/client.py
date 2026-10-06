"""
client.py solo maneja requests (GET, POST, ...) y respuestas
"""

import base64
import logging
import requests

from time import perf_counter
from math import ceil
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from typing import Optional, Dict, List, Any

from .config import DOMAIN, API_KEY
from .endpoints.jobs.jobs_api import JobsAPI
from .endpoints.jobs.reports.reports_api import ReportAPI
from .endpoints.users import UsersAPI
from .endpoints.equipment import EquipmentAPI
from .endpoints.customers_api import CustomersAPI

logger = logging.getLogger(__name__)

class SynchroteamClient:
    """
    Client for synchroteam API
    """
    def __init__(self):
        auth_string = f"{DOMAIN}:{API_KEY}"
        encoded_auth_string = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        self.base_url = f"https://{DOMAIN}.synchroteam.com/Api/v3" 
        self.cookies_file = "session.cookies"
    
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
    def _request(
                self, 
                method:   str, 
                endpoint: str, 
                headers:  Optional[Dict] = None,
                data:     Optional[Dict] = None, 
                params:   Optional[Dict] = None,
                debug_headers: Optional[bool] = False
        ) -> Any:
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        logger.debug("[%s] Request to %s", method.upper(), url)
        
        if headers:
            self.headers.update(headers)
            
        start_time = perf_counter()

        response = self.session.request(
            method = method.upper(),
            url = url,
            headers = self.headers, 
            json = data, 
            params = params
        )

        # miliseconds
        duration_ms = (perf_counter() - start_time) * 1000 

        logger.debug(
            "[%s] %s -> %s (%.2fs)", 
            method.upper(),
            url,
            response.status_code,
            duration_ms
        )
        
        try:
            response.raise_for_status()
        except requests.HTTPError:
            logger.exception(
                "[%s] %s failed -> %s",
                method.upper(),
                endpoint,
                response.status_code
            )
            raise
    
        # http headers
        #  daily quota remaining
        quota_remainig = response.headers.get("X-Quota-Remaining")

        if quota_remainig:
            logger.debug("Remaining quota: %s", quota_remainig)
            if quota_remainig < 5000:
                logger.warning("Low Synchroteam quota remaining: %s", quota_remainig)
        
        #  all headers
        if debug_headers:
            logger.debug("Response headers: %s", dict(response.headers))
        
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

        start_time = perf_counter()

        if extra_params is None:
            extra_params = {}
        
        initial_params = extra_params.copy()
        initial_params.update({
            "page": 1,
            "pageSize": page_size
        })

        response = self.session.get(url, headers=headers, params=initial_params, timeout=30)
        response.raise_for_status()
        data = response.json()

        total_records = int(data.get("recordsTotal", 0))
        total_pages = ceil(total_records / page_size)


        logger.info(
            "Total records: %s from %s page. Route: %s Params: %s",
            total_records,
            total_pages,
            url,
            initial_params
        )        

        records = data.get("data", [])

        def fetch_page(page: int):
            params = extra_params.copy()
            params.update({"page": page, "pageSize": page_size})
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            return response.json().get("data", [])
        
        # descargar en paralelo desde la página 2 hasta la última
        if total_pages <= 1:
            return records
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(fetch_page, page) 
                for page in range(2, total_pages + 1)
            ]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading records"):
                try: 
                    records.extend(future.result())
                except Exception:
                    logger.exception("Error fetching page")

        
        elapsed_time = perf_counter() - start_time

        logger.info(
            "Records downloading completed in %.2f seconds. Total records: %s",
            elapsed_time,
            len(records)
        )
        
        return records
    

    def test_connection(self) -> Any:
        """
        Realiza una petición básica para verificar autenticación y conectividad con la API.
        """
        return self._request("GET", "/job/list")