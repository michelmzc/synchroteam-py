import traceback
import requests
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

class ReportAPI:
    def __init__(self, client: "SynchroteamClient"): # type: ignore
        self.client = client

     # Obtiene el reporte de un trabajo por ID de trabajo o por número de trabajo
    def get_job_report(self, job_id=None, job_num=None):
        endpoint = f"/jobReport/details"        

        if job_id != None: params = { "id": job_id }
        if job_num != None: params = { "num" : job_num }

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

    # A partir de un diccionario de reporte obtiene el estado de inspección
    def get_report_item(self, report: Dict, item_name: str) -> Any:
        item_found = None
        for item in report["items"]:
            if item.get("name") == item_name:
                item_found = item
                return item_found
        return None
        
    def get_subregister(self, job_id: str) -> Any:
        report = self.get_job_report(job_id=job_id)
        if report is None:
            return {"is_subregister": None}
        else:
            report = report[0]
        inspection_status = self.get_report_item(report=report, item_name="Estado Inspeccion")
        print(inspection_status)
        if inspection_status is not None:
            if inspection_status["value"] == "Sub-Registro":
                return {
                    "is_subregister": True, 
                    **report,      
                }
            else:
                return {
                    "is_subregister": False,
                    **report,
                }
        else:
            return { "is_subregister": None }
    
    # a partir de una lista de trabajos, busca reportes, encuentra subregistros y devuelve información relacionada a clientes y tecnicos
    def get_subregisters(self, jobs_list: List[Dict], folder: str = "/files/jobs") -> List[Dict]:
        # Función para procesar cada job
        def process_job(job):
            try:
                # Filtrar si es Sub-Registro
                report = self.get_subregister(job_id=job["id"])
                
                if report["is_subregister"] is None:
                    return None
                elif report["is_subregister"] is False:
                    return False
                else:

                    try:
                        # obtener info adicional
                        customer = self.client.users.get_customer(customer_id=job["customer"]["id"])
                    except Exception as e:
                        customer = "Error"
                        print(f"ERROR: {e}")
                        traceback.print_exc()
                        input()

                    technician_team = self.client.users.get_user_by_id(job["technician"]["id"])["teams"][0]
                    team_city = technician_team.rsplit("-", 1)[-1].strip()                    
                    # Combinar observaciones
                    obs = [
                        i.get("value", "")
                        for i in report.get("items", [])
                        if i.get("name") in ("Observacion", "Observacion 2")
                    ]
                    obs = " | ".join(filter(None, obs))                    

                    return {
                        **job,
                        "report": report,
                        "customer_info": customer,
                        "technician_info": team_city,
                        "obs": obs
                    }
            except Exception as e:
                print(f"Error procesando job {job['id']}: {e}")
                traceback.print_exc()
                return None

        # Ejecutar en paralelo
        sub_registers = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_job, job): job for job in jobs_list}
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Revisando reportes para encontrar subregistros ...", unit="jobs"):
                result = future.result()
                if result:
                    sub_registers.append(result)

        return sub_registers