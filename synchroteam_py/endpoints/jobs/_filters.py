"""
Filtros de datos para trabajos.
Estos procesan los datos entregados por la API en tiempo de ejecución.
"""

from datetime import datetime, timezone, timedelta
from ...utils import parse_utc

from typing import List


def get_jobs_by_last_hour_modified(jobs_list: List) -> List:
    """
     Analiza una lista de trabajos y devuelve los modificados la última hora
    """
    # calcular el momento hace una hora
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    print(f"One hour ago was: { one_hour_ago} and now is { now }  ")
        
    # convertir y y filtrar trabajos modificados la ultima hora
    recent_jobs = []
    for job in jobs_list:
        modified_dt = parse_utc(job["dateModified"])
            
        if modified_dt and one_hour_ago <= modified_dt <= now:
            print(f"One hour ago was {one_hour_ago} and modified job was {modified_dt} and now is { now }")
            recent_jobs.append(job)
        
    # ordenar por fecha de modificación descente (más recientes primero)
    recent_jobs.sort(key=lambda j: datetime.fromisoformat(j["dateModified"].rstrip('Z')), reverse=True)

    print(f"Total of modified last hour {len(recent_jobs)}")

    return recent_jobs  


def check_status_job(job_list: List, status: str):
    """
    Revisa estados de una lista de trabajo y devuelve los concordantes al solicitado.
    Ej: "completed", "validated", entre otros.
    """
    checked_jobs = []
    for job in job_list:
        job_status = job.get("status")
        if job_status == status:
            checked_jobs.append(job)
        
    return checked_jobs

def target_photo_filter(photos, target_photo):
    for photo in photos["jobPhoto"]:
        if photo["comment"] == target_photo:
            return photo
    return None

    