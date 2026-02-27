from __future__ import annotations
import numpy as np
import pandas as pd

def winsorize(s: pd.Series, p=0.01) -> pd.Series:
    if s is None or len(s)==0:
        return s
    lo = s.quantile(p)
    hi = s.quantile(1-p)
    return s.clip(lo, hi)

def zscore_cs(s: pd.Series) -> pd.Series:
    x = s.astype(float)
    return (x - x.mean())/(x.std()+1e-9)

def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    denom = np.sqrt((ra**2).sum() * (rb**2).sum())
    if denom < 1e-12:
        return 0.0
    return float(np.dot(ra, rb) / denom)

def cross_section_ic(panel: pd.DataFrame, factor: str, label_col="label_fwd", min_cs=6, winsor_p=0.01):
    times = panel.index.get_level_values(0).unique()
    ics = []
    for t in times:
        g = panel.xs(t, level=0)
        if factor not in g.columns or label_col not in g.columns:
            continue
        x = winsorize(g[factor].astype(float), winsor_p)
        y = g[label_col].astype(float)
        df = pd.concat([x,y], axis=1).dropna()
        if len(df) < min_cs:
            continue
        ics.append((t, spearman(df.iloc[:,0].values, df.iloc[:,1].values)))
    ic = pd.Series({t:v for t,v in ics}).sort_index()
    if len(ic)==0:
        return ic, 0.0, 0.0, 0.0
    mean_ic = float(ic.mean())
    std_ic = float(ic.std())
    icir = mean_ic/(std_ic+1e-9)
    pos = float((ic>0).mean())
    return ic, mean_ic, icir, pos
