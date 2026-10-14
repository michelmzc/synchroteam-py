"""
Config file for wrapper
"""
import os
from dotenv import load_dotenv 

load_dotenv()

try:
    DOMAIN = os.getenv("SYNCHROTEAM_DOMAIN")
except Exception as e:
    DOMAIN = None

try: 
    API_KEY = os.getenv("SYNCHROTEAM_API_KEY")
except Exception as e:
    API_KEY = None