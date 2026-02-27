from __future__ import annotations
import numpy as np
import pandas as pd
from .base import Strategy, StrategySignal

def zscore_cs(s: pd.Series):
    x = s.astype(float)
    return (x-x.mean())/(x.std()+1e-9)

class FactorCSStrategy(Strategy):
    def __init__(self, name: str, factor_weights: pd.Series, top_n=3, bottom_n=3, leverage=1.0):
        self.name = name
        self.fw = factor_weights.copy()
        self.top_n = int(top_n)
        self.bottom_n = int(bottom_n)
        self.leverage = float(leverage)

    def update_factor_weights(self, w: pd.Series):
        self.fw = w.copy()

    def on_bar(self, t, panel_t: pd.DataFrame) -> StrategySignal:
        score = pd.Series(0.0, index=panel_t.index)
        for f, w in self.fw.items():
            if f in panel_t.columns:
                score += float(w) * zscore_cs(panel_t[f])
        s = score.replace([np.inf, -np.inf], np.nan).dropna()
        wgt = pd.Series(0.0, index=panel_t.index)
        if len(s) >= self.top_n + self.bottom_n:
            longs = s.nlargest(self.top_n).index
            shorts = s.nsmallest(self.bottom_n).index
            wgt.loc[longs] = +(self.leverage/2)/self.top_n
            wgt.loc[shorts] = -(self.leverage/2)/self.bottom_n
            meta = {"status":"ok"}
        else:
            meta = {"status":"insufficient_cs"}
        return StrategySignal(self.name, wgt, meta)
