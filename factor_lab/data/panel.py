from __future__ import annotations
import pandas as pd
from factor_lab.factors.registry import ensure_sorted, align_to_base, default_registry

def build_base_index(all_sym_data: dict, syms: list[str], base_tf="15m", index_mode="union", min_history=200):
    idxs = []
    for sym in syms:
        df = ensure_sorted(all_sym_data.get(sym, {}).get(base_tf))
        if df is None or len(df) < min_history:
            continue
        idxs.append(df.index)
    if not idxs:
        raise ValueError("no base_tf data for any symbol")
    base = idxs[0]
    for x in idxs[1:]:
        base = base.union(x) if index_mode=="union" else base.intersection(x)
    return base.sort_values()

def build_panel(all_sym_data: dict, base_tf="15m", fwd_period=4, index_mode="union"):
    syms = sorted(list(all_sym_data.keys()))
    reg = default_registry()
    base_index = build_base_index(all_sym_data, syms, base_tf=base_tf, index_mode=index_mode)

    frames = []
    for sym in syms:
        sd = {tf: ensure_sorted(df) for tf, df in all_sym_data[sym].items() if df is not None}
        dfb = sd.get(base_tf)
        if dfb is None or len(dfb) < 50:
            continue
        out = pd.DataFrame(index=base_index)
        out["open"]  = align_to_base(dfb["open"].astype(float), base_index)
        out["close"] = align_to_base(dfb["close"].astype(float), base_index)
        if "volume" in dfb.columns:
            out["volume"] = align_to_base(dfb["volume"].astype(float), base_index)
        fac = reg.compute_for_symbol(sd, base_index)
        out = pd.concat([out, fac], axis=1)
        # label aligned to actual execution window: enter at open[t+1], exit at open[t+1+fwd_period]
        # so return = close[t+1+fwd_period] / close[t+1] - 1  (open ≈ close for 24/7 crypto)
        out["label_fwd"] = out["close"].shift(-(fwd_period + 1)) / (out["close"].shift(-1) + 1e-12) - 1.0
        out["symbol"] = sym
        frames.append(out.reset_index().rename(columns={"index":"time"}))

    panel = pd.concat(frames, ignore_index=True)
    panel["time"] = pd.to_datetime(panel["time"])
    panel = panel.set_index(["time","symbol"]).sort_index()
    return panel, reg
