# Configure you enviroment variables or .env

from synchroteam_py import SynchroteamClient

client = SynchroteamClient()

jobs_types = client.jobs.get_job_types()

print(jobs_types)