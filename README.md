# Synchroteam API python wrapper

This proyect is a wrapper for Synchroteam API V3.
## Setup

Clone the repository and create virtual env:

```bash
python -m venv venv
```

Activate virtual env (Windows OS example):

```bash
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& c:\Users\User\Desktop\synchroteam-py\venv\Scripts\Activate.ps1)
```

Then install dependencies:

```bash
pip install -e .
```

Python >=3.8 and pip updated are required.



## Create .env file
```bash
SYNCHROTEAM_DOMAIN=
SYNCHROTEAM_API_KEY=

SYNCHROTEAM_USER=
SYNCHROTEAM_PASSWORD=
SYNCHROTEAM_WEB_URL=
```

Synchroteam user, password and web_url are used for download Jobs PDFs RPA and are optional.


## Run example.py

```python
# First configure you enviroment variables or .env file and activate

from synchroteam_py import SynchroteamClient

client = SynchroteamClient()

# Test API connetction
try:
    print(client.test_connection())
    print("Connected")
except Exception as error:
    print("Error in connection", e)

# Test of jobs endpoint
jobs_types = client.jobs.get_job_types()

print(jobs_types)

```

```bash
python example.py
```
