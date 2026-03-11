"""
MeanReversionStrategy — contrarian cross-sectional strategy.
Buys recent losers, shorts recent winners (opposite of momentum).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .base import Strategy, StrategySignal


class MeanReversionStrategy(Strategy):
    """Rank by recent return and go contrarian."""

    def __init__(self, name: str, signal_col: str = "ret_1h",
                 top_n: int = 3, bottom_n: int = 3, leverage: float = 1.0):
        self.name = name
        self.signal_col = signal_col
        self.top_n = int(top_n)
        self.bottom_n = int(bottom_n)
        self.leverage = float(leverage)

    def on_bar(self, t, panel_t: pd.DataFrame) -> StrategySignal:
        col = self.signal_col if self.signal_col in panel_t.columns else "close"
        s = panel_t[col].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
        wgt = pd.Series(0.0, index=panel_t.index)
        if len(s) >= self.top_n + self.bottom_n:
            # contrarian: buy recent losers, short recent winners
            longs = s.nsmallest(self.top_n).index
            shorts = s.nlargest(self.bottom_n).index
            wgt.loc[longs] = +(self.leverage / 2) / self.top_n
            wgt.loc[shorts] = -(self.leverage / 2) / self.bottom_n
            meta = {"status": "ok"}
        else:
            meta = {"status": "insufficient_cs"}
        return StrategySignal(self.name, wgt, meta)
