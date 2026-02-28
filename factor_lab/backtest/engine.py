from __future__ import annotations
import numpy as np
import pandas as pd
from factor_lab.backtest.execution import ExecutionSimulator

class BacktestEngine:
    def __init__(self, panel: pd.DataFrame, base_tf="15m", fwd_period=4, capital=1e6, exec_sim: ExecutionSimulator|None=None):
        self.panel = panel.sort_index()
        self.times = self.panel.index.get_level_values(0).unique()
        self.syms = self.panel.index.get_level_values(1).unique()
        self.fwd_period = int(fwd_period)
        self.capital = float(capital)
        self.exec = exec_sim or ExecutionSimulator()
        self.pos = pd.Series(0.0, index=self.syms)
        self.equity = 1.0

    def step(self, t, w_target: pd.Series):
        syms = self.syms
        wp = self.pos.reindex(syms).fillna(0.0)
        wt = w_target.reindex(syms).fillna(0.0)
        # remove net exposure (market neutral)
        wt = wt - wt.mean()

        idx = self.times.get_indexer([t])[0]
        if idx+1+self.fwd_period >= len(self.times):
            return {"status":"no_future", "equity": float(self.equity)}

        t_entry = self.times[idx+1]
        t_exit  = self.times[idx+1+self.fwd_period]

        entry_open = self.panel.xs(t_entry, level=0).reindex(syms)["open"].astype(float)
        exit_open  = self.panel.xs(t_exit, level=0).reindex(syms)["open"].astype(float)

        g_now = self.panel.xs(t, level=0).reindex(syms)
        # Convert volume to USD-denominated ADV (base_volume × price) for impact model consistency
        if "volume" in g_now.columns:
            price_now = g_now["close"].astype(float).fillna(g_now["open"].astype(float)).replace(0, np.nan).fillna(1.0)
            adv = (g_now["volume"].astype(float).abs() * price_now).fillna(1e6).replace(0, 1e6)
        else:
            adv = pd.Series(1e6, index=syms)
        vol = pd.Series(0.01, index=syms)
        if idx > 0:
            t_prev = self.times[idx-1]
            c_now = self.panel.xs(t, level=0).reindex(syms)["close"].astype(float)
            c_prev= self.panel.xs(t_prev, level=0).reindex(syms)["close"].astype(float)
            vol = (c_now/(c_prev+1e-12)-1.0).abs().fillna(0.01).clip(lower=1e-6)

        w_exec, cost, entry_eff, breakdown = self.exec.execute(wp, wt, entry_open, adv, vol, self.capital)

        r_i = (exit_open/(entry_eff+1e-12)-1.0).replace([np.inf,-np.inf], np.nan).fillna(0.0)
        ret_hold = float(np.nansum(w_exec.values * r_i.values))
        ret = ret_hold - float(cost)

        self.pos = w_exec
        self.equity *= (1.0 + ret)

        return {
            "status":"ok",
            "t": str(t),
            "t_entry": str(t_entry),
            "t_exit": str(t_exit),
            "ret_hold": ret_hold,
            "ret": ret,
            "equity": float(self.equity),
            "cost_breakdown": breakdown
        }
