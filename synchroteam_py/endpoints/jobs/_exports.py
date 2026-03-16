from pathlib import Path
import csv 

def suberegisters_to_csv(subregisters, day, month, year, route):
        # Definimos los campos que necesitamos
        fields = [
            "job_id",
            "job_number",
            "status",
            "type",
            "service",
            "client name",
            "inspection_status",
            "completed_date",
            "company",
            "technician_user_id",
            "zone",
            "obs"
        ]

        # ruta para csv
        csv_file = route / f"subregisters_{day}-{month}-{year}.csv"

        with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            for job in subregisters:
                #obtener estado de inspección forma segura
                report_items = job.get("report", [{}]).get("items", [])
                estado_inspeccion = next(
                    (item.get("value") for item in report_items if item.get("name") == "Estado Inspeccion"),
                    None
                )
                empresa = next(
                    (
                        field.get("value")
                        for field in job.get("customer_info", {}).get("customFieldValues", [])
                        if field.get("label") == "Empresa"
                    ),
                    None
                )
                row = {
                    "job_id": job.get("id"),
                    "job_number": job.get("num"),
                    "status": job.get("status"),
                    "type": job.get("type", {}).get("name"),
                    "service": job.get("customer", {}).get("myId"),
                    "client name": job.get("customer", {}).get("name"),
                    "inspection_status": estado_inspeccion,
                    "completed_date": job.get("actualEnd"),
                    "company": empresa,
                    "technician_user_id": job.get("technician", {}).get("login"),
                    "zone": job.get("technician_info"),
                    "obs": job.get("obs")
                }
                writer.writerow(row)