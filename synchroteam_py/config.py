"""
Config file for wrapper
"""
import os
from dotenv import load_dotenv 

load_dotenv()

DOMAIN = os.getenv("SYNCHROTEAM_DOMAIN")
API_KEY = os.getenv("SYNCHROTEAM_API_KEY")