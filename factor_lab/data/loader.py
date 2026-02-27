from __future__ import annotations
from datetime import datetime, timedelta, timezone
import pandas as pd
from .binance import fetch_klines
from .cache import cache_key, read_cache, write_cache

INTERVAL_MAP = {"1m":"1m","5m":"5m","15m":"15m","1h":"1h"}

def load_all_sym_data(cfg) -> dict:
    if cfg.data.source == "local":
        if not cfg.data.local_path:
            raise ValueError("data.local_path is required for local source")
        panel = pd.read_parquet(cfg.data.local_path)
        return {"__panel__": panel}

    b = cfg.data.binance
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=b.days)
    start_ms = int(start.timestamp()*1000)
    end_ms = int(end.timestamp()*1000)

    all_sym_data = {}
    for sym in cfg.universe.symbols:
        all_sym_data[sym] = {}
        for tf in cfg.timeframes:
            k = cache_key(sym, tf, start_ms, end_ms)
            df = None
            if cfg.data.cache.enabled:
                df = read_cache(cfg.data.cache.dir, k)
            if df is None:
                df = fetch_klines(sym, INTERVAL_MAP[tf], start_ms, end_ms,
                                  base_url=b.base_url, proxy=(b.proxy or None),
                                  timeout_s=b.timeout_s, rate_limit_sleep_ms=b.rate_limit_sleep_ms)
                if cfg.data.cache.enabled and df is not None and len(df):
                    write_cache(cfg.data.cache.dir, k, df)
            all_sym_data[sym][tf] = df
    return all_sym_data
