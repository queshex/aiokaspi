from datetime import datetime, timezone, timedelta

def get_current_time() -> str:
    tz = timezone(timedelta(hours=5))
    dt = datetime.now(tz)
    formatted_dt = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + dt.strftime('%z')
    return formatted_dt
