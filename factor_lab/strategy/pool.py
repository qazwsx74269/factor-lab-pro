from __future__ import annotations
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from .base import Strategy, StrategySignal

@dataclass
class StrategyState:
    strat: Strategy
    pnl_hist: list[float] = field(default_factory=list)
    weight: float = 0.0
    active: bool = True

def sharpe_like(x: list[float]):
    if len(x) < 10:
        return 0.0
    a = np.asarray(x, dtype=float)
    m = float(np.mean(a))
    s = float(np.std(a))
    return m/(s+1e-9)

class StrategyPool:
    def __init__(self, max_active=6, score_window=192, replace_each_n_steps=96, seed=1):
        self.max_active = int(max_active)
        self.score_window = int(score_window)
        self.replace_each_n_steps = int(replace_each_n_steps)
        self.rng = np.random.default_rng(seed)
        self.states: list[StrategyState] = []
        self.step_i = 0

    def add(self, strat: Strategy, weight=0.0):
        self.states.append(StrategyState(strat=strat, weight=float(weight), active=True))

    def active(self):
        return [s for s in self.states if s.active]

    def update_pnl(self, strat_name: str, ret: float):
        for st in self.states:
            if st.strat.name == strat_name:
                st.pnl_hist.append(float(ret))
                if len(st.pnl_hist) > self.score_window:
                    st.pnl_hist = st.pnl_hist[-self.score_window:]
                return

    def scores(self):
        rows=[]
        for st in self.states:
            sc = sharpe_like(st.pnl_hist[-self.score_window:])
            rows.append((st.strat.name, st.active, st.weight, sc, len(st.pnl_hist)))
        df = pd.DataFrame(rows, columns=["name","active","weight","score","n"])
        return df.sort_values("score", ascending=False)

    def allocate_equal(self):
        act = self.active()
        if not act:
            return
        w = 1.0/len(act)
        for st in act:
            st.weight = w

    def maybe_replace(self, factory_fn):
        self.step_i += 1
        if self.step_i % self.replace_each_n_steps != 0:
            return {"did_replace": False}

        act = self.active()
        if len(act) <= 1:
            return {"did_replace": False}

        # drop worst score
        scores = [(sharpe_like(st.pnl_hist[-self.score_window:]), i) for i, st in enumerate(self.states) if st.active]
        scores.sort(key=lambda x: x[0])
        worst_score, worst_idx = scores[0]
        # replace with new candidate
        self.states[worst_idx].active = False

        new = factory_fn()
        self.add(new, weight=0.0)
        # keep active count capped
        act2 = self.active()
        if len(act2) > self.max_active:
            # deactivate extra lowest-score actives
            df = self.scores()
            keep = set(df[df["active"]].head(self.max_active)["name"].values)
            for st in self.states:
                if st.active and st.strat.name not in keep:
                    st.active = False
        self.allocate_equal()
        return {"did_replace": True, "dropped": self.states[worst_idx].strat.name, "dropped_score": worst_score, "added": new.name}
