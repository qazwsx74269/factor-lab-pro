from __future__ import annotations
import os
import pandas as pd

def cache_key(symbol: str, tf: str, start_ms: int, end_ms: int) -> str:
    return f"{symbol}__{tf}__{start_ms}__{end_ms}.parquet"

def read_cache(cache_dir: str, key: str):
    path = os.path.join(cache_dir, key)
    if os.path.exists(path):
        return pd.read_parquet(path)
    return None

def write_cache(cache_dir: str, key: str, df: pd.DataFrame):
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, key)
    df.to_parquet(path)
    return path
