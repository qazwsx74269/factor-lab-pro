from __future__ import annotations
import numpy as np
import pandas as pd

class ExecutionSimulator:
    def __init__(self, fee_rate=0.0005, slippage=0.0002, impact_c=0.10, impact_p=0.50, n_slices=4):
        self.fee_rate=float(fee_rate)
        self.slippage=float(slippage)
        self.impact_c=float(impact_c)
        self.impact_p=float(impact_p)
        self.n_slices=int(n_slices)

    def execute(self, w_prev: pd.Series, w_new: pd.Series, entry_price: pd.Series, adv: pd.Series, vol: pd.Series, capital: float):
        syms = w_prev.index.union(w_new.index).union(entry_price.index)
        wp = w_prev.reindex(syms).fillna(0.0).astype(float)
        wn = w_new.reindex(syms).fillna(0.0).astype(float)
        px = entry_price.reindex(syms).ffill().bfill().fillna(0.0).astype(float)
        advv = adv.reindex(syms).fillna(1e6).astype(float).replace(0,np.nan).fillna(1e6)
        volv = vol.reindex(syms).fillna(0.01).astype(float).clip(lower=1e-6)

        dw = (wn - wp)
        notional = np.abs(dw.values)*float(capital)
        total_notional = float(np.sum(notional))

        fee_amt = self.fee_rate * total_notional
        slip_amt = self.slippage * total_notional

        impact_rate = self.impact_c * volv.values * ((notional/(advv.values*self.n_slices+1e-12))**self.impact_p)
        impact_amt = float(np.sum(impact_rate * notional))

        total_cost_amt = fee_amt + slip_amt + impact_amt
        cost_total = total_cost_amt/float(capital)

        direction = np.sign(dw.values)
        eff_rate = self.slippage + impact_rate
        entry_eff = pd.Series(px.values*(1.0 + direction*eff_rate), index=syms)

        breakdown = dict(
            notional=total_notional,
            fee_cost=fee_amt/float(capital),
            slip_cost=slip_amt/float(capital),
            impact_cost=impact_amt/float(capital),
            total_cost=float(cost_total),
            dw_l1=float(np.sum(np.abs(dw.values))),
        )
        return wn, float(cost_total), entry_eff, breakdown
