from __future__ import annotations
import numpy as np
import pandas as pd

def ensure_sorted(df: pd.DataFrame):
    if df is None or len(df)==0:
        return df
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    return df

def align_to_base(s: pd.Series, base_index: pd.DatetimeIndex) -> pd.Series:
    s = s.copy()
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.reindex(base_index, method="ffill")

def rsi(series: pd.Series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(com=period-1, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=period-1, adjust=False).mean()
    return 100 - (100 / (1 + gain/(loss+1e-9)))

class FactorRegistry:
    def __init__(self):
        self._items = {}  # name -> (fn, required_tfs, desc)

    def register(self, name: str, fn, tfs: list[str], desc: str=""):
        self._items[name] = (fn, list(tfs), desc)

    def names(self):
        return list(self._items.keys())

    def compute_for_symbol(self, sym_data: dict, base_index: pd.DatetimeIndex) -> pd.DataFrame:
        sd = {tf: ensure_sorted(df) for tf, df in sym_data.items() if df is not None}
        out = {}
        for name, (fn, tfs, _) in self._items.items():
            if any(tf not in sd or sd[tf] is None or len(sd[tf])==0 for tf in tfs):
                out[name] = pd.Series(np.nan, index=base_index)
                continue
            try:
                s = fn(sd, base_index)
                out[name] = s.reindex(base_index)
            except Exception:
                out[name] = pd.Series(np.nan, index=base_index)
        return pd.DataFrame(out, index=base_index)

def default_registry() -> FactorRegistry:
    reg = FactorRegistry()

    def f_ret_1h(sd, base):
        return align_to_base(sd["1h"]["close"].astype(float).pct_change(1), base)

    def f_ret_4h(sd, base):
        return align_to_base(sd["1h"]["close"].astype(float).pct_change(4), base)

    def f_rsi_14_1h(sd, base):
        return align_to_base(rsi(sd["1h"]["close"].astype(float), 14), base)

    def f_trend_align(sd, base):
        signs = []
        for tf, p in [("1m",5), ("5m",3), ("15m",1), ("1h",1)]:
            s = np.sign(sd[tf]["close"].astype(float).pct_change(p))
            signs.append(align_to_base(s, base))
        return pd.concat(signs, axis=1).sum(axis=1)

    def f_bb_pos(sd, base):
        c = sd["15m"]["close"].astype(float)
        ma = c.rolling(20).mean()
        st = c.rolling(20).std()
        return ((c-(ma-2*st))/(4*st+1e-9) - 0.5).reindex(base)

    def f_zscore_20(sd, base):
        c = sd["15m"]["close"].astype(float)
        ma = c.rolling(20).mean()
        st = c.rolling(20).std()
        return ((c-ma)/(st+1e-9)).reindex(base)

    def f_macd_signal(sd, base):
        c = sd["15m"]["close"].astype(float)
        e12 = c.ewm(span=12, adjust=False).mean()
        e26 = c.ewm(span=26, adjust=False).mean()
        macd = e12 - e26
        sig = macd.ewm(span=9, adjust=False).mean()
        return ((macd - sig)/(c+1e-9)).reindex(base)

    def f_vol_ratio(sd, base):
        df = sd["15m"]
        if "volume" not in df.columns:
            return pd.Series(np.nan, index=base)
        v = df["volume"].astype(float)
        return (v/(v.rolling(20).mean()+1e-9) - 1.0).reindex(base)

    def f_taker_ratio(sd, base):
        df = sd["15m"]
        if "taker_base" not in df.columns or "volume" not in df.columns:
            return pd.Series(np.nan, index=base)
        return (df["taker_base"].astype(float)/(df["volume"].astype(float)+1e-9) - 0.5).reindex(base)

    reg.register("ret_1h", f_ret_1h, ["1h"], "1h 1bar return")
    reg.register("ret_4h", f_ret_4h, ["1h"], "1h 4bar return")
    reg.register("trend_align", f_trend_align, ["1m","5m","15m","1h"], "sum of directions across tfs")
    reg.register("rsi_14_1h", f_rsi_14_1h, ["1h"], "RSI(14) on 1h mapped to base")
    reg.register("bb_pos", f_bb_pos, ["15m"], "BB position (20,2)")
    reg.register("z_score_20", f_zscore_20, ["15m"], "Z-score(20)")
    reg.register("macd_signal", f_macd_signal, ["15m"], "MACD hist normalized")
    reg.register("vol_ratio", f_vol_ratio, ["15m"], "vol/ma20 - 1")
    reg.register("taker_ratio", f_taker_ratio, ["15m"], "taker_base/vol - 0.5")

    return reg
