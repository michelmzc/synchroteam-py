import time
import requests
from math import ceil
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import timezone, datetime
from dateutil.parser import parse 
from typing import Optional, Dict, List


# función para obtener todos los registros de una consulta desde su paginación
def get_all_records(
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

import csv
from pathlib import Path
# función que agrega timezone a un date string
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
    
#función que toma export CSV y los consolida en uno final
def consolidate_csvs(
        input_dir="static/export_csv", 
        output_file="static/consolidado.csv"
    ) -> Optional[List[Dict[str, str]]]:
    
    """
        Consolida todos los CSV dentro de input_dir en un solo CSV output_file.
        Retorna la lista de filas consolidadas o None si no hay archivos.
    """
       
    input_path = Path(input_dir)
    csv_files = list(input_path.glob("*.csv"))

    if not csv_files:
        print("No se encontraron archivos CSV")
        return None
    
    consolidated_rows: List[Dict[str, str]] = []
    headers: Optional[List[str]] = None

    for file in csv_files:
        with open(file, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=",")
            if headers is None:
                if reader.fieldnames is None:
                    raise ValueError(f"No se pudieron obtener encabezados del archivo CSV")
                headers = list(reader.fieldnames)
            for row in reader:
                consolidated_rows.append(row)
    
    if headers is None:
        print("No se pudieron determinar los headers")
        return None
    
    outputh_path = Path(output_file)
    outputh_path.parent.mkdir(parents=True, exist_ok=True)

    with open(outputh_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers, delimiter=",")
        writer.writeheader()
        writer.writerows(consolidated_rows)
    
    print(f"Consolidado guardo en: {output_file}")

    return consolidated_rows

from functools import wraps
from flask import request, jsonify

def validate_dates(param_names):
    """
    Decorador para validad parámetros de fecha (path o query).
    Convierte los parámetros a datetime si están en formato DD-MM-YYYY.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            for name in param_names:
                # buscar en path params (kwargs) o query params (?date=01-01-2025)
                date_str = kwargs.get(name) or request.args.get(name)

                if not date_str:
                    return jsonify({
                        "error":f"El parámetro '{name}' es requerido"
                    }), 400
                try:
                    # convertir y reemplazar en kwargs
                    kwargs[name] = datetime.strptime(date_str, "%d-%m-%Y")
                except ValueError:
                    return jsonify({
                        "error": f"Formato Inválido para '{name}', use DD-MM-YYYY"
                    }), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator