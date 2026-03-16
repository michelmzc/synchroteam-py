# Synchroteam API python wrapper

This proyect is a wrapper for Synchroteam API.
## Setup

Clone the repository and then:

```bash
pip install -e .
```

Python >=3.8 y pip updated are required.

## Enviroment variables and optional .env file
```bash
SYNCHROTEAM_DOMAIN=
SYNCHROTEAM_API_KEY=
SYNCHROTEAM_USER=
SYNCHROTEAM_PASSWORD=
SYNCHROTEAM_WEB_URL=
```

Synchroteam user, password and web_url are used for download Jobs PDFs and are optional.


## Example of use

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