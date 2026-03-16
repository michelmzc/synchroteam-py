# Synchroteam API python wrapper

This proyect is a wrapper for Synchroteam API.

## Enviroment variables and optional .env file
```
SYNCHROTEAM_DOMAIN=
SYNCHROTEAM_API_KEY=
SYNCHROTEAM_USER=
SYNCHROTEAM_PASSWORD=
SYNCHROTEAM_WEB_URL=
```

Synchroteam user, password and web_url are used for download Jobs PDFs and are optional.


## Example of use

```
# First configure you enviroment variables or .env file and activate

from synchroteam_py import SynchroteamClient

client = SynchroteamClient()

jobs_types = client.jobs.get_job_types()

print(jobs_types)

```