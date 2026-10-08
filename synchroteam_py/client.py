"""
client.py 

Client for Synchroteam API
"""
from __future__ import annotations

import base64
import logging
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from time import perf_counter
from math import ceil
from concurrent.futures import ThreadPoolExecutor
from types import TracebackType
from typing import Optional, Dict, List, Any, Type

from .config import DOMAIN, API_KEY
from .endpoints.jobs.jobs_api import JobsAPI
from .endpoints.jobs.reports.reports_api import ReportAPI
from .endpoints.users import UsersAPI
from .endpoints.equipment import EquipmentAPI
from .endpoints.customers_api import CustomersAPI

logger = logging.getLogger(__name__)


# constants
API_PATH = "/Api/v3"
DEFAULT_TIMEOUT = 30
DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_WORKERS = 10
DEFAULT_POOL_SIZE = 20
LOW_QUOTA_THRESHOLD = 5000
QUOTA_HEADER = "X-Quota-Remaining"
LOG_BODY_LIMIT = 500
RETRY_TOTAL = 3
RETRY_BACKOFF_FACTOR = 1
RETRY_STATUS_CODES = (429, 500, 502, 503, 504)


class SynchroteamClient:
    """
    Class of client for synchroteam API
    """
    def __init__(
            self, 
            domain: Optional[str] = None, 
            api_key: Optional[str] = None, 
            timeout: int = DEFAULT_TIMEOUT, 
            pool_size: int = DEFAULT_POOL_SIZE
        ) -> None:
        
        domain = domain or DOMAIN
        api_key = api_key or API_KEY

        auth_string = f"{domain}:{api_key}"
        encoded_auth_string = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

        self.base_url = f"https://{domain}.synchroteam.com{API_PATH}" 
        self.timeout = timeout

        # by Synchroteam documentation
        self.headers = {
            "Authorization":f"Basic {encoded_auth_string}",
            "Content-Type":"application/json",
            "Accept":"text/json",
            "Cache-Control":"no-cache"
        }

        # creation by function
        self.session = self._build_session(self.headers, pool_size)

        # submodules instace
        self.reports = ReportAPI(self)
        self.jobs = JobsAPI(self, report=self.reports)
        self.users = UsersAPI(self)
        self.equipment = EquipmentAPI(self)
        self.customers = CustomersAPI(self)

    @staticmethod
    def _build_session(headers: Dict[str, str], pool_size:int) -> requests.Session:
        """ Crea la sesión con reinttos solo para GET """
        retry = Retry(
            total=RETRY_TOTAL,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            status_forcelist=RETRY_STATUS_CODES,
            allowed_methods=frozenset(["GET"]),
            # permite que _raise_for_status maneje el error final en vez de lanzar RetryError
            raise_on_status=False 
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=pool_size,
            pool_maxsize=pool_size
        )
        session = requests.Session()
        session.headers.update(headers)
        session.mount("https://", adapter)

        return session

    def close(self) -> None:
        "Cierrra la sesión y libera las conexiones"
        self.session.close()

    def __enter__(self) -> SynchroteamClient:
        return self

    def __exit__(
            self, 
            exc_type: Optional[Type[BaseException]], 
            exc_value: Optional[BaseException], 
            traceback: Optional[TracebackType]
        ) -> None:
        self.close()


    def _request(
                self, 
                method:   str, 
                endpoint: str, 
                headers:  Optional[Dict[str, str]] = None,
                data:     Optional[Dict[str, Any]] = None, 
                params:   Optional[Dict[str, Any]] = None,
                debug_headers: bool = False
        ) -> Any:
        """ 
            Núcleo de peticiones HTTP 

            Ejecuta una petición y devuelve el JSON de la respuesta (o None si el cuerpo viene vacío).    
        """

        method = method.upper()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        logger.debug("[%s] Request to %s", method, url)
        
        start_time = perf_counter()
        
        # combina headears de la petición los headers de sesión
        response = self.session.request(
            method = method,
            url = url,
            headers = headers, 
            json = data, 
            params = params,
            timeout = self.timeout
        )

        # miliseconds
        duration_ms = (perf_counter() - start_time) * 1000 

        logger.debug(
            "[%s] %r -> %s (%.2fms)", 
            method,
            url,
            response.status_code,
            duration_ms
        )

        # revisión de cuota previa para cubrir error 429

        self._check_quota(response)

        if debug_headers:
            logger.debug("Response headers: %s", dict(response.headers))

        self._raise_for_status(method, endpoint, response)

        return self._parse_body(response)

    @staticmethod
    def _check_quota(response: requests.Response) -> None:
        """ Registra la cuota diaria restante y avisa si es baja """
        raw_quota = response.headers.get(QUOTA_HEADER)
        if raw_quota is None:
            return

        try:
            quota_remaining = int(raw_quota)
        except ValueError:
            logger.warning("Invalid %s header: %s", QUOTA_HEADER, raw_quota)
            return

        logger.debug("Remaining quota: %s", quota_remaining)
        if quota_remaining < LOW_QUOTA_THRESHOLD:
            logger.warning("Low Synchroteam quota remainig: %s", quota_remaining)

    @staticmethod
    def _raise_for_status(method: str, endpoint: str, response: requests.Response) -> None:
        """ Lanza HTTPError registrando el cuerpo (truncado) para depurar. """
        try:
            response.raise_for_status()
        except requests.HTTPError:
            logger.error(
                "[%s] %r failed -> %s | body: %s",
                method,
                endpoint,
                response.status_code,
                response.text[:LOG_BODY_LIMIT]
            )
            raise

    @staticmethod
    def _parse_body(response: requests.Response) -> Any:
        """ Devuelve el JSON o None si no hay cuerpo (204, algunos DELETE)"""
        if not response.content:
            return None
        return response.json()

    # paginación
    def get_all_records(
            self, 
            endpoint: str, 
            extra_params: Optional[Dict[str, Any]] = None, 
            page_size: int = DEFAULT_PAGE_SIZE,         
            max_workers: int = DEFAULT_MAX_WORKERS,
            headers: Optional[Dict[str, str]] = None
        ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros desde una ruta dada, soporta paginación y threading.

        Argumentos: 
                endpoint (str): De la ruta a pedir (sin parámetros).
                headers (dict): Parámetros para la cabecera de la solicitud.
                extra_params (dict): Parámetros adicionales para la consulta.
                page_size (int): Tamaño de registros por página (máximo API Synchroteam)
                max_workers (int): Número de hilos por concurrencia
        Retorna:
                list: Lista combinada con todos los registros filtrados
        """
        if page_size < 1:
            raise ValueError("page_size must be >= 1")


        start_time = perf_counter()
        base_params = dict(extra_params or {})

        def fetch_page(page: int) -> Dict[str, Any]:
            params = {**base_params, "page": page, "pageSize": page_size}
            logger.debug("Fetching page %s of %r", page, endpoint)
            return self._request("GET", endpoint, headers=headers, params=params) or {}

        first_page = fetch_page(1)
        records: List[Dict[str, Any]] = list(first_page.get("data", []))

        total_records = int(first_page.get("recordsTotal", 0))
        total_pages = ceil(total_records / page_size)

        logger.info(
            "Total records: %s from %s pages. Route: %r Params: %s",
            total_records,
            total_pages,
            endpoint,
            base_params
        )

        if total_pages > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for page_data in executor.map(fetch_page, range(2, total_pages + 1)):
                    records.extend(page_data.get("data", []))

        logger.info(
            "Records downloading completed in %.2f seconds. Total records: %s",
            perf_counter() - start_time,
            len(records)
        )

        return records
    

    def test_connection(self) -> Any:
        """
        Realiza una petición básica para verificar autenticación y conectividad con la API.
        """
        return self._request("GET", "/job/list")