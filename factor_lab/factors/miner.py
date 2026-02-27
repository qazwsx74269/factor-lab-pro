from __future__ import annotations
import pandas as pd
from factor_lab.research.ic import cross_section_ic

class FactorMiningResult:
    def __init__(self, table: pd.DataFrame, valid_factors: list[str]):
        self.table = table
        self.valid_factors = valid_factors

def mine_factors(panel: pd.DataFrame, factor_names: list[str], cfg_mining, cfg_research, label_col="label_fwd"):
    rows = []
    for f in factor_names:
        ic, mean_ic, icir, pos = cross_section_ic(
            panel, f, label_col=label_col, min_cs=cfg_mining.min_cs, winsor_p=cfg_research.winsor_p
        )
        rows.append((f, mean_ic, icir, pos, len(ic)))
    tab = pd.DataFrame(rows, columns=["factor","ic_mean","icir","ic_pos","n_ic"]).sort_values("icir", key=lambda s: s.abs(), ascending=False)

    valid = tab[(tab["ic_mean"].abs() >= cfg_mining.ic_min_abs) & (tab["icir"].abs() >= cfg_mining.icir_min_abs)]
    valid_factors = list(valid["factor"].head(cfg_mining.max_valid).values)
    return FactorMiningResult(tab, valid_factors)
