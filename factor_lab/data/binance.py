from __future__ import annotations
import time
import requests
import pandas as pd

def fetch_klines(symbol: str, interval: str, start_ms: int, end_ms: int,
                 base_url: str = "https://api.binance.com",
                 proxy: str | None = None,
                 timeout_s: int = 20,
                 rate_limit_sleep_ms: int = 200,
                 limit: int = 1000) -> pd.DataFrame:
    """Spot public endpoint /api/v3/klines."""
    s = requests.Session()
    if proxy:
        s.proxies.update({"http": proxy, "https": proxy})
    url = base_url.rstrip("/") + "/api/v3/klines"

    out = []
    cur = start_ms
    while cur < end_ms:
        r = s.get(url, params=dict(symbol=symbol, interval=interval, startTime=cur, endTime=end_ms, limit=limit),
                  timeout=timeout_s)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        out.extend(data)
        last_open = int(data[-1][0])
        if last_open == cur:
            break
        cur = last_open + 1
        time.sleep(rate_limit_sleep_ms / 1000.0)

    if not out:
        return pd.DataFrame()

    df = pd.DataFrame(out, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_asset_volume","num_trades",
        "taker_buy_base","taker_buy_quote","ignore"
    ])
    df["time"] = pd.to_datetime(df["close_time"], unit="ms")
    for c in ["open","high","low","close","volume","taker_buy_base"]:
        df[c] = df[c].astype(float)
    df = df.set_index("time").sort_index()
    df = df.rename(columns={"taker_buy_base": "taker_base"})
    return df[["open","high","low","close","volume","taker_base"]]
