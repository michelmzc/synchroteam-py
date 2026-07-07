"""
Function to download job content
"""
import requests
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

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
    photos: Dict,
    folder_route: Path,
    target: Optional[str] = None,
    max_workers: Optional[int] = 5
) -> str:
    """ 
    Download all job photos with threading usage.
    Params:
        - photos: Returned dict of job photos endpoint.
        - folder_route: Custom route to create a folder.
        - target: Get a custom targeted photo by it's comment (name)
    
    """

    job_folder = Path(folder_route)
    job_folder.mkdir(parents=True, exist_ok=True)
    
    # Download photos in parallel with threading
    with ThreadPoolExecutor(max_workers) as executor:
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


    return str(job_folder)