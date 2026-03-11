"""
TopFactorStrategy — uses only the single highest-weight factor to generate signals.
More concentrated/aggressive than FactorCSStrategy.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .base import Strategy, StrategySignal


def zscore_cs(s: pd.Series) -> pd.Series:
    x = s.astype(float)
    return (x - x.mean()) / (x.std() + 1e-9)


class TopFactorStrategy(Strategy):
    """Bet only on the single best factor by absolute weight."""

    def __init__(self, name: str, factor_weights: pd.Series,
                 top_n: int = 3, bottom_n: int = 3, leverage: float = 1.0):
        self.name = name
        self.fw = factor_weights.copy()
        self.top_n = int(top_n)
        self.bottom_n = int(bottom_n)
        self.leverage = float(leverage)

    def update_factor_weights(self, w: pd.Series):
        self.fw = w.copy()

    def on_bar(self, t, panel_t: pd.DataFrame) -> StrategySignal:
        # pick the single factor with highest abs weight
        available = [(f, w) for f, w in self.fw.items() if f in panel_t.columns]
        wgt = pd.Series(0.0, index=panel_t.index)
        if not available:
            return StrategySignal(self.name, wgt, {"status": "no_factor"})

        best_f, best_w = max(available, key=lambda x: abs(x[1]))
        direction = 1.0 if best_w >= 0 else -1.0
        score = direction * zscore_cs(panel_t[best_f])
        s = score.replace([np.inf, -np.inf], np.nan).dropna()

        if len(s) >= self.top_n + self.bottom_n:
            longs = s.nlargest(self.top_n).index
            shorts = s.nsmallest(self.bottom_n).index
            wgt.loc[longs] = +(self.leverage / 2) / self.top_n
            wgt.loc[shorts] = -(self.leverage / 2) / self.bottom_n
            meta = {"status": "ok", "factor": best_f}
        else:
            meta = {"status": "insufficient_cs"}

        return StrategySignal(self.name, wgt, meta)
