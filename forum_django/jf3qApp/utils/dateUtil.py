from datetime import datetime

def get_now_ts():
    current_time = datetime.now()
    cts = current_time.strftime('%Y-%m-%d %H:%M:%S')
    return cts