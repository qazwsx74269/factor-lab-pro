from __future__ import annotations
import datetime as dt

def ts_now_str():
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")
