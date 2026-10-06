from datetime import timezone
from dateutil.parser import parse 

# función que agrega timezone a un date string
@staticmethod
def parse_utc(dt_str):
    if not dt_str:
        return None 
    try:
        dt = parse(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt 
    except Exception as e:
        print(f"Error parsing: {dt_str} -> {e}")
        return None
