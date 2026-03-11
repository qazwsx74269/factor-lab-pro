"""
VolScaledCSStrategy — factor cross-sectional strategy with volatility scaling.
Same as FactorCSStrategy but allocates more weight to low-volatility symbols
(inverse-vol sizing within the long and short legs).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .base import Strategy, StrategySignal


def zscore_cs(s: pd.Series) -> pd.Series:
    x = s.astype(float)
    return (x - x.mean()) / (x.std() + 1e-9)


class VolScaledCSStrategy(Strategy):
    """Factor CS strategy with inverse-volatility position sizing."""

    def __init__(self, name: str, factor_weights: pd.Series,
                 vol_col: str = "vol_ratio",
                 top_n: int = 3, bottom_n: int = 3, leverage: float = 1.0):
        self.name = name
        self.fw = factor_weights.copy()
        self.vol_col = vol_col
        self.top_n = int(top_n)
        self.bottom_n = int(bottom_n)
        self.leverage = float(leverage)

    def update_factor_weights(self, w: pd.Series):
        self.fw = w.copy()

    def _inv_vol_weights(self, syms: pd.Index, panel_t: pd.DataFrame) -> pd.Series:
        """Inverse-vol sizing: lower vol → higher weight."""
        if self.vol_col in panel_t.columns:
            vol = panel_t.loc[syms, self.vol_col].astype(float).clip(lower=1e-6)
        else:
            vol = pd.Series(1.0, index=syms)
        inv = 1.0 / vol
        return inv / inv.sum()

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
            long_w = self._inv_vol_weights(longs, panel_t)
            short_w = self._inv_vol_weights(shorts, panel_t)
            wgt.loc[longs] = +(self.leverage / 2) * long_w
            wgt.loc[shorts] = -(self.leverage / 2) * short_w
            meta = {"status": "ok"}
        else:
            meta = {"status": "insufficient_cs"}

        return StrategySignal(self.name, wgt, meta)
