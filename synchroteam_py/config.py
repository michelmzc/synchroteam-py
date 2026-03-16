
import os
from dotenv import load_dotenv 

load_dotenv()

API_URL = os.getenv("SYNCHROTEAM_API_URL")
API_KEY = os.getenv("SYNCHROTEAM_API_KEY")
DOMAIN = os.getenv("SYNCHROTEAM_DOMAIN")
USER = os.getenv("SYNCHROTEAM_USER")
PASSWORD = os.getenv("SYNCHROTEAM_PASSWORD")
WEB_URL = os.getenv("SYNCHROTEAM_WEB_URL")