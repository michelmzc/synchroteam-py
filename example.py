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