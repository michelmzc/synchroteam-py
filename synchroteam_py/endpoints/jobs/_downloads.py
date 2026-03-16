"""
Funciones de descarga de archivos: JPG, PNG, PDF, entre otros.
"""
import os
import time
import requests
import re
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By 
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

def imagenes_ya_descargadas(folder: Path) -> bool:
    """Retorna True si ya existen imágenes en la carpeta"""
    return any(f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png")
               for f in folder.iterdir())

def renumerar_imagenes_por_indice(folder: Path):
    con_numero = []
    sin_numero = []

    for f in folder.iterdir():
        if not f.is_file():
            continue

        match = re.match(r"^\s*(\d+)\s*[\.\-_ ]\s*(.+)$", f.name)
        if match:
            num = int(match.group(1))
            resto = match.group(2)
            con_numero.append((num, f, resto))
        else:
            sin_numero.append(f)

    con_numero.sort(key=lambda x: x[0])

    renames = []
    contador = 1

    for _, archivo, resto in con_numero:
        nuevo = folder / f"{contador}. {resto}"
        renames.append((archivo, nuevo))
        contador += 1

    for archivo in sin_numero:
        nuevo = folder / f"{contador}{archivo.suffix or '.jpg'}"
        renames.append((archivo, nuevo))
        contador += 1

    for original, destino in renames:
        if original != destino:
            shutil.move(str(original), destino)

def download_single_photo(photo, folder) -> bool:
    """ Descarga una foto individual """

    url = photo.get("url")
    comment = photo.get("comment", "").strip()

    if comment:
        filename = comment + ".jpg"
    else:
        filename = ".jpg"   # queda como archivo sin nombre → se renumera después

    safe_filename = "".join(
        c for c in filename if c.isalnum() or c in (" ", ".", "_")
    ).rstrip()

    folder = Path(folder)
    file_path = folder / safe_filename

    try:
        content = requests.get(url).content
        with open(file_path, "wb") as file:
            file.write(content)
        print(f"Saved photo: {file_path.name}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_job_photos(
    photos,
    service_id: str,
    folder: Path,
    target: str = None
) -> str:
    """ Descarga todas las fotos y luego las renumera (idempotente) """

    job_folder = Path(folder)
    job_folder.mkdir(parents=True, exist_ok=True)

    # ======================================================
    # ⛔ SI YA EXISTEN IMÁGENES → NO HACER NADA
    # ======================================================
    if imagenes_ya_descargadas(job_folder):
        print(f"⏭️ Fotos ya descargadas para {service_id}, se omite descarga")
        return str(job_folder)

    # ======================================================
    # DESCARGA
    # ======================================================
    with ThreadPoolExecutor(max_workers=5) as executor:
        if target:
            futures = [
                executor.submit(download_single_photo, photo, job_folder)
                for photo in photos["jobPhoto"][target]
            ]
        else:
            futures = [
                executor.submit(download_single_photo, photo, job_folder)
                for photo in photos["jobPhoto"]
            ]

        for f in futures:
            f.result()

    # ======================================================
    # 🔢 RENÚMERAR SOLO SI SE DESCARGÓ
    # ======================================================
    renumerar_imagenes_por_indice(job_folder)

    return str(job_folder)



def download_job_pdf(job_id: str, service_id: str, folder: str="files/jobs/pdfs"):
        """
        Descarga PDFs
        """
        prefs = {
            "download.default_directory": str(folder),   # Carpeta donde guardará los PDFs
            "download.prompt_for_download": False,       # No mostrar diálogo de descarga
            "download.directory_upgrade": True,          # Sobrescribir si existe
            "plugins.always_open_pdf_externally": True,  # Descargar PDFs en lugar de abrirlos
            "download.open_pdf_in_system_reader": False  # No abrir pdf luego de descargar
        }
        options = webdriver.ChromeOptions()
        options.add_experimental_option("prefs", prefs)
        driver = webdriver.Chrome(options=options)

        # Abrir la página de login
        driver.get("https://controldeenergia.synchroteam.com/app/Account/Login")

        load_dotenv()
        user = os.getenv("SYNCHROTEAM_USER")
        password = os.getenv("SYNCHROTEAM_PASSWORD")
        if user and password:
            # Llenar el formulario de login
            driver.find_element(By.ID, "UserName").send_keys(user)
            driver.find_element(By.ID, "Password").send_keys(password)
        else:
            return False
        # Click en el botón de login
        driver.find_element(By.ID, "ImageButton2").click()

        time.sleep(5)  # esperar a que cargue el panel tras login   

        try: 
            #folder = folder.lstrip("/\\")  # elimina slashes iniciales
            job_folder = folder
            job_folder.mkdir(parents=True, exist_ok=True)

            url = f"https://controldeenergia.synchroteam.com/app/Jobs/PDF/{ job_id }" 
            driver.get(url)
            time.sleep(2)
            print(f"[OK] PDF descargado para trabajo {service_id}")        

            
            pdf_files = list(job_folder.glob(f".pdf"))
            if pdf_files:
                pdf_file = pdf_files[0]  # el primero que encontró
                new_path = job_folder / f"{service_id}.pdf"
                pdf_file.rename(new_path)
        
        except Exception as e:
            print(f"[ERROR] PDF no ha sido descargado para {service_id}: {e}")
            return False
        
        driver.quit()
        return True

def download_jobs_pdfs(jobs: List, folder: str="files/jobs/pdfs"):
    """
    Descarga PDFs en lote secuencial para una lista de trabajos, usando un solo navegador.
    No se detiene por errores individuales.
    Evita descargas si el PDF ya existe y limpia duplicados descargados.
    """

    folder = Path(folder).absolute()
    folder.mkdir(parents=True, exist_ok=True)

    prefs = {
        "download.default_directory": str(folder),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "download.open_pdf_in_system_reader": False
    }

    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=options)

    # Login
    driver.get("https://controldeenergia.synchroteam.com/app/Account/Login")

    load_dotenv()
    user = os.getenv("SYNCHROTEAM_USER")
    password = os.getenv("SYNCHROTEAM_PASSWORD")

    if not user or not password:
        print("❌ No hay credenciales en .env")
        driver.quit()
        return False

    driver.find_element(By.ID, "UserName").send_keys(user)
    driver.find_element(By.ID, "Password").send_keys(password)
    driver.find_element(By.ID, "ImageButton2").click()

    time.sleep(5)

    # Procesar cada trabajo sin detener la ejecución
    for job in jobs:

        try:
            # ----------------------------------------------------
            # 1) Verificar SI YA EXISTE el PDF antes de descargar
            # ----------------------------------------------------
            job_folder = folder / f"CC_{job.service_id}" / f"Trabajo_{job.number}"
            final_pdf_path = job_folder / f"{job.service_id}.pdf"

            if final_pdf_path.exists():
                print(f"✔️ PDF ya existe para {job.service_id}, se omite descarga.")
                continue

            print(f"⬇️ Descargando PDF para trabajo {job.id} ...")

            # ----------------------------------------------------
            # 2) Descargar PDF normalmente
            # ----------------------------------------------------
            url = f"https://controldeenergia.synchroteam.com/app/Jobs/PDF/{job.id}"
            driver.get(url)
            time.sleep(2)

            pdf_file = _wait_for_pdf_download(folder)

            if not pdf_file:
                print(f"❌ No se descargó PDF para {job.id}")
                continue

            print(f"[OK] PDF descargado para trabajo {job.service_id}")

            # ----------------------------------------------------
            # 3) Mover el archivo descargado a su carpeta final
            # ----------------------------------------------------
            job_folder.mkdir(parents=True, exist_ok=True)

            try:
                pdf_file.rename(final_pdf_path)

            except FileExistsError:
                # Ya existe → limpiar duplicado
                print(f"⚠️ Duplicado detectado para {job.service_id}, eliminando archivo descargado.")
                try:
                    pdf_file.unlink()  # borrar el PDF recién descargado
                except:
                    pass
                continue

            except Exception as move_err:
                print(f"⚠️ Error moviendo PDF de {job.id}: {move_err}")
                # limpiar PDF descargado
                if pdf_file.exists():
                    pdf_file.unlink()
                continue

        except Exception as e:
            print(f"[ERROR] PDF no ha sido descargado para {job.service_id}: {e}")
            continue  # ← seguir siempre

    driver.quit()
    return True

def _wait_for_pdf_download(folder: Path, timeout=40):
    """
    Espera a que Chrome termine de descargar un PDF.
    Devuelve el archivo final.
    """

    start = time.time()

    while time.time() - start < timeout:
        files = list(folder.glob("*.pdf"))
        partial = list(folder.glob("*.crdownload"))

        if files and not partial:
            return files[0]

        time.sleep(1)

    return None