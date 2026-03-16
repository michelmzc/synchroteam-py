"""
Usa client.py para obtener Trabajos, aplicar filtros, parseos, etc.
"""
import logging
import traceback

from tqdm import tqdm
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Any, Dict, Optional, List
from tabulate import tabulate
import pandas as pd

from .reports.reports_api import ReportAPI
from ._filters import check_status_job, get_jobs_by_last_hour_modified, target_photo_filter
from ._downloads import download_job_photos, download_single_photo, download_job_pdf, download_jobs_pdfs
from ._exports import suberegisters_to_csv
from ..utils import get_all_records
from concurrent.futures import ThreadPoolExecutor, as_completed



class JobsAPI:
    def __init__(self, client: "SynchroteamClient", report: "ReportAPI"): # type: ignore
        self.client = client
        self.report =  ReportAPI(client)
    
    # Obtiene tipos de trabajos definidos en Synchroteam
    def get_job_types(self):
        endpoint = f"/jobtype/list"        
        return self.client._request("GET", endpoint)

    # Obtiene trabajos segun parametros
    def get_jobs(self, params: Optional[Dict] = None) -> List[Dict]:
        endpoint = "/job/list"
        return self.client._request("GET", endpoint, params=params)
    
    # Obtiene todos los trabajos que se soliciten según parámetros, usa threading
    def get_all_jobs(self, extra_params: Optional[Dict]) -> List[Dict]:
        return get_all_records(
            url = f"{self.client.base_url}/job/list",
            headers = self.client.headers,
            extra_params = extra_params
        )
    
    # Obtiene un trabajo por su ID
    def get_job_by_id(self, id: Optional[str] = None, num: Optional[int] = None) -> Any:
        if id:
            return self.client._request("GET", f"/job/details", params={"id":id})
        if num:
            return self.client._request("GET", f"/job/details", params={"num": num})

    def get_jobs_by_time_between(
            self,
            start_time: str, 
            end_time: str, 
            extra_params: Optional[Dict] = None
        ) -> List:

        params = {         
            "dateFrom": start_time,
            "dateTo":   end_time
        }

        if extra_params:
            params.update(extra_params)

        jobs = self.get_all_jobs(extra_params=params)

        return jobs  

    # obtiene el estado de tareas completedas y validadas con ACP
    def get_day_synchroteam_acp_satus(self, target_date):
        start_datetime = datetime.combine(target_date, dt_time.min).strftime("%d/%m/%Y, %H:%M:%S")
        end_datetime   = datetime.combine(target_date, dt_time.max).strftime("%d/%m/%Y, %H:%M:%S")
        
        trifasic_jobs  = self.get_jobs_by_time_between(start_datetime, end_datetime, extra_params={'type_name':'Inspeccion Trifasica'})
        monofasic_jobs = self.get_jobs_by_time_between(start_datetime, end_datetime, extra_params={'type_name': 'Inspeccion Monofasica'})

        job_3f_completed = check_status_job(trifasic_jobs, "validated")
        job_3f_validated = check_status_job(trifasic_jobs, "completed")
        job_1f_completed = check_status_job(monofasic_jobs, "completed")
        job_1f_validated = check_status_job(monofasic_jobs, "validated")

        total_3f = len(job_3f_completed) + len(job_1f_completed)
        total_1f = len(job_1f_validated) + len(job_3f_validated)

        total_validated = len(job_1f_validated) + len(job_3f_validated)
        total_completed = len(job_1f_completed) + len(job_3f_completed)
        total = total_completed + total_validated

        percent = (total_validated * 100) / total
    
        data = [
            ["Trifásico", len(job_3f_completed), len(job_3f_validated)],
            ["Monofásico", len(job_1f_completed), len(job_1f_validated)],
            ["Totales", total_3f, total_1f]
        ]

        headers = ["Tipo de inspección", "Completados", "Validados"]
        print(f"\n Reporte del día: {target_date} \n")
        print(tabulate(data, headers=headers, tablefmt="github"))

        print(f"\nTotal de trabajos: {total}")
        print(f"Porcentaje de trabajos validados: {percent:.0f}% \n")

        return [f"Para el día: {target_date}", data]

    def get_photos(self, job_id: str = "", target_photo: str = "") -> Any:
        endpoint = f"/job/photos"        
        params = {"id":job_id}
        photos = self.client._request("GET", endpoint, params=params)

        if target_photo:
            photos = target_photo_filter(photos, target_photo)
            if photos: return photos
            else: return "Photo not found"

        return photos

    def subregisters_csv_export(self, day, month, year):
        
        day_datetime = datetime.strptime(f"{day}-{month}-{year}", "%d-%m-%Y")
        start_datetime = datetime.combine(day_datetime, dt_time.min).strftime("%d/%m/%Y, %H:%M:%S")
        end_datetime   = datetime.combine(day_datetime, dt_time.max).strftime("%d/%m/%Y, %H:%M:%S")
        
          
        trifasic_jobs = self.get_jobs_by_time_between(start_time=start_datetime, end_time=end_datetime, extra_params={"type_name": "Inspeccion Trifasica"})
        monofasic_jobs = self.get_jobs_by_time_between(start_time=start_datetime, end_time=end_datetime, extra_params={"type_name": "Inspeccion Monofasica"})
        
        validated_jobs = check_status_job(trifasic_jobs, status="validated") + check_status_job(monofasic_jobs, status="validated")
        completed_jobs = check_status_job(trifasic_jobs, status="completed") + check_status_job(monofasic_jobs, status="completed")
        jobs = validated_jobs + completed_jobs        
        
        print(f"Total de trabajos a consultar: {len(jobs)}")
        #input("Presionar [ENTER] para continuar...")
        subregisters = self.report.get_subregisters(jobs_list=jobs)
        print(f"Cuantity of subregisters: {len(subregisters)}")
        

        # carpetas por año, mes, dia
        path = self.client.route / "files" / "subregisters" / year / month / day
        path.mkdir(parents=True, exist_ok=True)
        
        try:
            suberegisters_to_csv(subregisters, day, month, year, route=path)
        except Exception as e:
            print(f"ERROR: {e}")
    
        return subregisters

    def get_jobs_by_last_hour_modified(self, jobs):
        return get_jobs_by_last_hour_modified(jobs_list=jobs)
    
    def download_single_photo(self, photo, folder):
        return download_single_photo(photo, folder)       

    def download_job_photos(self, job_id, service_id, folder):
        photos = self.get_photos(job_id)
        return download_job_photos(photos, service_id, folder)


    def download_pdfs_from_services(self, job_id: str, service_id: str, folder="static/img"):
        output_dir = Path(folder)
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            download_job_pdf(job_id=job_id, service_id=service_id, folder=folder)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False
        
        
    def download_subregisters_files_for_acp(self, day, month, year, workers=5):
        """
        1. Descargar fotos en paralelo (multithread)
        2. Descargar PDFs en cola secuencial usando Selenium
        """

        folder_path = self.client.route / "files" / "subregisters" / year / month / day
        csv_filepath = folder_path / f"subregisters_{day}-{month}-{year}.csv"

        # Asegurarnos que la carpeta exista (donde guardaremos todo, incluido el log)
        folder_path.mkdir(parents=True, exist_ok=True)

        # === CONFIG LOGS (robusto) ===
        log_file = folder_path / f"{day}-{month}-{year}.log"

        # Obtener logger raíz y reconfigurarlo (limpiar handlers previos)
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # eliminar handlers previos para que la nueva configuración aplique siempre
        if logger.hasHandlers():
            for h in list(logger.handlers):
                logger.removeHandler(h)
                h.close()

        # Crear handlers nuevos
        fh = logging.FileHandler(str(log_file), encoding="utf-8")
        sh = logging.StreamHandler()

        formatter = logging.Formatter("%(asctime)s — %(levelname)s — %(message)s")
        fh.setFormatter(formatter)
        sh.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(sh)

        # Ahora logging.info escribirá en archivo + consola
        logging.info("===== INICIO DE LOTE =====")
        logging.info(f"Archivo CSV: {csv_filepath}")

        # === CARGAR CSV ===
        filename = csv_filepath
        folder_export = folder_path

        if not filename.exists():
            logging.error(f"El archivo no existe: {filename}")
            raise FileNotFoundError(f"El archivo no existe: {filename}")

        df = pd.read_csv(filename)
        

        if "status" not in df.columns:
            logging.error(f"La columna 'status' no existe en {csv_filepath}")
            raise ValueError(f"La columna 'status' no existe en {csv_filepath}")

        df = df[df["status"] == "validated"]
        logging.info(f"Trabajos filtrados: {len(df)}")

        # === NORMALIZAR NUMÉRICOS A STRING ===
        for col in ["service", "job_number", ]:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: str(int(float(x))) if pd.notna(x) else "")


        
        # === ETAPA 1: DESCARGAR FOTOS MULTITHREAD ===
        def download_photos_only(row):
            job_id = row["job_id"]
            service_id = row["service"]
            job_number = row["job_number"]

            job_folder = (
                folder_export /
                f"CC_{service_id}" /
                f"Trabajo_{job_number}"
            )
            job_folder.mkdir(parents=True, exist_ok=True)

            logging.info(f"[FOTOS] Job {job_id} → carpeta {job_folder}")

            
            try:
                
                self.download_job_photos(
                    job_id=job_id,
                    service_id=service_id,
                    folder=job_folder,
                )
                

                logging.info(f"✓ Fotos de {job_id} descargadas")
                return {
                    "id": job_id,
                    "service": service_id,
                    "number": job_number
                }

            except Exception as e:
                err = f"ERROR al descargar fotos de {job_id}: {e}"
                logging.error(err)
                logging.error(traceback.format_exc())
                return None
        
        
        
        # --- Ejecutar fotos con hilos ---
        jobs_for_pdf = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(download_photos_only, row) for _, row in df.iterrows()]

            for future in tqdm(as_completed(futures), total=len(futures), desc=f"Descargando fotos ({workers} workers)"):
                result = future.result()
                if result:
                    jobs_for_pdf.append(result)
        
        logging.info(f"FOTOS OK: {len(jobs_for_pdf)}")

        # =====================================================================
        # === ETAPA 2: DESCARGAR PDFs SECUENCIALMENTE (COLA) ================
        # =====================================================================

        if len(jobs_for_pdf) == 0:
            logging.warning("No hay trabajos para descargar PDFs")
            return True

        logging.info("=== Iniciando descarga secuencial de PDFs ===")

        # Convertir a objetos "simples" para Selenium
        class SimpleJob:
            def __init__(self, j):
                self.id = j["id"]
                self.service_id = j["service"]
                self.number = j["number"]

        jobs_queue = [SimpleJob(j) for j in jobs_for_pdf]

        # LLAMAMOS LA FUNCIÓN QUE YA CORREGIMOS (usa selenium y descarga 1 a 1)
        download_jobs_pdfs(jobs_queue, folder=folder_export)

        logging.info("===== FIN DE LOTE =====")
        print("\n==== LOTE COMPLETO ====\n")

        return True