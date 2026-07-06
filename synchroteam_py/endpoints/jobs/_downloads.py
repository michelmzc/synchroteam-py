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

def download_single_photo(photo: Dict, folder: str, name: str) -> bool:
    """ Download a single photo """

    url = photo.get("url")
    comment = photo.get("comment", "").strip()

    if name:
        filename = str(name) + ".jpg"
    elif comment:
        filename = comment + ".jpg"
    else:
        filename = ".jpg"   # without name

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

    # Si ya existen imágenes no hacer nada, mejorable a comprobar imagenes cargadas
    if imagenes_ya_descargadas(job_folder):
        print(f"⏭️ Fotos ya descargadas para {service_id}, se omite descarga")
        return str(job_folder)

    # Descarga
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

    
    renumerar_imagenes_por_indice(job_folder)

    return str(job_folder)