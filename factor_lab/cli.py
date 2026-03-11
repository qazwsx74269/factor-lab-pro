from __future__ import annotations
import os, json
from collections import deque
import numpy as np
import typer
import pandas as pd

from factor_lab.utils.logging import setup_logger
from factor_lab.utils.time import ts_now_str
from factor_lab.config.load import load_cfg
from factor_lab.data.loader import load_all_sym_data
from factor_lab.data.panel import build_panel
from factor_lab.factors.miner import mine_factors
from factor_lab.optimizer.factor_weight import FactorWeightOptimizer, ridge_premia, orthogonalize, shrink_cov
from factor_lab.strategy.factor_cs import FactorCSStrategy
from factor_lab.strategy.momentum import MomentumStrategy
from factor_lab.strategy.mean_reversion import MeanReversionStrategy
from factor_lab.strategy.vol_scaled import VolScaledCSStrategy
from factor_lab.strategy.top_factor import TopFactorStrategy
from factor_lab.strategy.pool import StrategyPool
from factor_lab.backtest.engine import BacktestEngine
from factor_lab.backtest.execution import ExecutionSimulator
from factor_lab.report.html import build_report
from factor_lab.report.index import build_runs_index

app = typer.Typer(add_completion=False)

@app.command()
def doctor():
    """Check runtime environment."""
    logger = setup_logger("doctor")
    logger.info("ok: logger")
    import cvxpy as cp
    logger.info("cvxpy=%s", cp.__version__)
    logger.info("done")

@app.command()
def run(config: str = typer.Option(..., "-c", "--config")):
    logger = setup_logger("run")
    cfg = load_cfg(config)

    runs_dir = os.getenv("FACTOR_LAB_RUNS_DIR", cfg.report.out_dir)
    run_id = ts_now_str()
    out_dir = os.path.join(runs_dir, run_id)
    os.makedirs(out_dir, exist_ok=True)

    logger.info("loading data...")
    all_sym = load_all_sym_data(cfg)

    # build panel
    panel, reg = build_panel(all_sym, base_tf=cfg.backtest.base_tf, fwd_period=cfg.backtest.fwd_period, index_mode=cfg.backtest.index_mode)
    factor_names = [c for c in reg.names() if c in panel.columns]
    logger.info("panel=%s factors=%d", panel.shape, len(factor_names))

    # mining
    if cfg.mining.enabled:
        mined = mine_factors(panel, factor_names, cfg.mining, cfg.research, label_col="label_fwd")
        valid_factors = mined.valid_factors
        factor_tab = mined.table
    else:
        valid_factors = factor_names
        factor_tab = pd.DataFrame({"factor": factor_names})

    if not valid_factors:
        logger.warning("no valid factors found; fallback to all")
        valid_factors = factor_names

    # online premia + optimizer
    opt = FactorWeightOptimizer()
    w_prev = pd.Series(0.0, index=valid_factors)

    # strategy pool
    pool = StrategyPool(max_active=cfg.strategy_pool.max_active,
                        score_window=cfg.strategy_pool.score_window,
                        replace_each_n_steps=cfg.strategy_pool.replace_each_n_steps)

    # seed pool with diverse strategies upfront
    init_fw = pd.Series({f: 1.0/len(valid_factors) for f in valid_factors})
    top_n, bot_n = cfg.backtest.top_n, cfg.backtest.bottom_n

    seed_strategies = [
        # 1. Multi-factor CS (equal weight, baseline)
        FactorCSStrategy(name="cs_equal", factor_weights=init_fw,
                         top_n=top_n, bottom_n=bot_n, leverage=1.0),
        # 2. Momentum (buy recent winners, short recent losers)
        MomentumStrategy(name="momentum", lookback_col="ret_1h",
                         top_n=top_n, bottom_n=bot_n, leverage=1.0),
        # 3. Mean reversion (contrarian)
        MeanReversionStrategy(name="mean_rev", signal_col="ret_1h",
                              top_n=top_n, bottom_n=bot_n, leverage=1.0),
        # 4. Vol-scaled factor CS (inv-vol sizing)
        VolScaledCSStrategy(name="vol_scaled", factor_weights=init_fw,
                            top_n=top_n, bottom_n=bot_n, leverage=1.0),
        # 5. Top-factor only (concentrated single-factor bet)
        TopFactorStrategy(name="top_factor", factor_weights=init_fw,
                          top_n=top_n, bottom_n=bot_n, leverage=1.0),
    ]
    # add up to max_active seeds
    for strat in seed_strategies[:cfg.strategy_pool.max_active]:
        pool.add(strat, weight=0.0)
    pool.allocate_equal()

    # backtest engine
    exec_sim = ExecutionSimulator(cfg.backtest.fee_rate, cfg.backtest.slippage, cfg.execution.impact_c, cfg.execution.impact_p, cfg.execution.n_slices)
    bt = BacktestEngine(panel, base_tf=cfg.backtest.base_tf, fwd_period=cfg.backtest.fwd_period, capital=cfg.backtest.capital, exec_sim=exec_sim)

    times = panel.index.get_level_values(0).unique()
    syms = panel.index.get_level_values(1).unique()

    ledger=[]
    # rolling premia buffer: use last ic_window cross-section premia for stable mu
    prem_window = cfg.mining.ic_window  # default 256 steps
    prem_buf: deque = deque(maxlen=prem_window)
    # rebalance period: only update factor weights & positions every fwd_period steps
    rebalance_period = cfg.backtest.fwd_period
    w_target_cached = pd.Series(0.0, index=syms)

    # to compute premia: for each time, do cross-sectional ridge on valid_factors
    for step_i, t in enumerate(times):
        g = panel.xs(t, level=0).reindex(syms)

        # build Z (zscore, winsor in miner; here keep simple)
        X = g[valid_factors].astype(float)
        Z = (X - X.mean())/(X.std()+1e-9)
        Z = Z.replace([float("inf"), float("-inf")], 0.0).fillna(0.0)

        if cfg.research.use_orthogonal:
            Z = orthogonalize(Z)

        r = g["label_fwd"].astype(float).replace([float("inf"), float("-inf")], 0.0).fillna(0.0)
        prem = ridge_premia(Z, r, ridge=1e-3).reindex(valid_factors).fillna(0.0)
        prem_buf.append(prem)

        # Only rebalance every fwd_period steps — no overlapping positions
        if step_i % rebalance_period != 0:
            ledger.append({
                "status": "hold",
                "equity": float(bt.equity),
                "step": step_i,
                "n_valid_factors": len(valid_factors),
                "top_factor": w_prev.abs().idxmax() if len(w_prev) else None,
                "top_factor_w": float(w_prev.abs().max()) if len(w_prev) else 0.0,
                "opt_diag": {"status": "hold"},
            })
            continue

        # Use rolling-average premia as mu — much more stable than single-period estimate
        if len(prem_buf) >= 4:
            prem_mat = pd.concat(list(prem_buf), axis=1)
            mu = prem_mat.mean(axis=1).reindex(valid_factors).fillna(0.0)
        else:
            mu = prem.copy()

        # rolling cov on Z for Sigma — guard against degenerate shapes
        try:
            cov_mat = np.cov(Z.values.T) if Z.shape[0] > Z.shape[1] else (Z.values.T @ Z.values) / max(1, Z.shape[0])
            if np.ndim(cov_mat) < 2:
                cov_mat = np.atleast_2d(cov_mat)
            Sigma = pd.DataFrame(shrink_cov(cov_mat, alpha=0.10),
                                 index=valid_factors, columns=valid_factors)
        except Exception:
            Sigma = pd.DataFrame(np.eye(len(valid_factors)) * 0.01,
                                 index=valid_factors, columns=valid_factors)

        # Warmup: don't trade until we have enough premia history for stable mu
        warmup_steps = min(64, prem_window // 4)
        if step_i < warmup_steps:
            ledger.append({
                "status": "warmup",
                "equity": float(bt.equity),
                "step": step_i,
                "n_valid_factors": len(valid_factors),
                "top_factor": None,
                "top_factor_w": 0.0,
                "opt_diag": {"status": "warmup"},
            })
            continue

        w_fac, diag = opt.solve(mu, Sigma, w_prev, cfg.optimizer)
        w_fac = w_fac.reindex(valid_factors).fillna(0.0)

        # Only update factor weights when signal is meaningful (not near-zero solver noise)
        if diag.get("status") not in ("fail", "near_zero"):
            w_prev = w_fac
        # else: keep w_prev from previous rebalance (hold current factor direction)

        # update pool strategies that are FactorCSStrategy
        for st in pool.active():
            if hasattr(st.strat, "update_factor_weights"):
                st.strat.update_factor_weights(w_prev)

        # If factor weights are all zero (no valid signal yet), skip rebalance this step
        # But still allow pool to grow/replace even when there's no signal
        if w_prev.abs().sum() < 1e-6:
            if cfg.strategy_pool.enabled:
                _ns_types = ["momentum", "mean_rev", "cs", "vol_scaled", "top_factor"]
                _fallback_fw = pd.Series({f: 1.0/len(valid_factors) for f in valid_factors})
                def factory():
                    k = len(pool.states)
                    stype = _ns_types[k % len(_ns_types)]
                    tn, bn = cfg.backtest.top_n, cfg.backtest.bottom_n
                    if stype == "momentum":
                        return MomentumStrategy(name=f"momentum_{k}", top_n=tn, bottom_n=bn)
                    elif stype == "mean_rev":
                        return MeanReversionStrategy(name=f"mean_rev_{k}", top_n=tn, bottom_n=bn)
                    elif stype == "vol_scaled":
                        return VolScaledCSStrategy(name=f"vol_scaled_{k}", factor_weights=_fallback_fw, top_n=tn, bottom_n=bn)
                    elif stype == "top_factor":
                        return TopFactorStrategy(name=f"top_factor_{k}", factor_weights=_fallback_fw, top_n=tn, bottom_n=bn)
                    else:
                        return FactorCSStrategy(name=f"cs_{k}", factor_weights=_fallback_fw, top_n=tn, bottom_n=bn)
                pool.maybe_replace(factory)
            ledger.append({
                "status": "no_signal",
                "equity": float(bt.equity),
                "step": step_i,
                "n_valid_factors": len(valid_factors),
                "top_factor": None,
                "top_factor_w": 0.0,
                "opt_diag": diag,
            })
            continue

        # combine strategy signals
        w_target = pd.Series(0.0, index=syms)
        for st in pool.active():
            sig = st.strat.on_bar(t, g)
            w_target = w_target.add(sig.weights.reindex(syms).fillna(0.0) * st.weight, fill_value=0.0)
        w_target_cached = w_target  # cache for non-rebalance steps

        meta = bt.step(t, w_target)
        meta["step"] = step_i
        meta["n_valid_factors"] = len(valid_factors)
        meta["top_factor"] = w_prev.abs().idxmax() if len(w_prev) else None
        meta["top_factor_w"] = float(w_prev.abs().max()) if len(w_prev) else 0.0
        meta["opt_diag"] = diag
        ledger.append(meta)

        # update strategy pnl with realized ret
        if meta.get("status") == "ok":
            # attribute ret equally to active strats as a simple proxy (can be improved to per-strat shadow pnl)
            r_step = float(meta.get("ret", 0.0))
            act = pool.active()
            if act:
                for st in act:
                    pool.update_pnl(st.strat.name, r_step * st.weight)

        # replacement: rotate through strategy types to keep diversity
        if cfg.strategy_pool.enabled:
            _strategy_types = ["cs", "momentum", "mean_rev", "vol_scaled", "top_factor"]
            def factory():
                k = len(pool.states)
                stype = _strategy_types[k % len(_strategy_types)]
                tn, bn = cfg.backtest.top_n, cfg.backtest.bottom_n
                if stype == "momentum":
                    return MomentumStrategy(name=f"momentum_{k}", lookback_col="ret_1h",
                                            top_n=tn, bottom_n=bn, leverage=1.0)
                elif stype == "mean_rev":
                    return MeanReversionStrategy(name=f"mean_rev_{k}", signal_col="ret_1h",
                                                 top_n=tn, bottom_n=bn, leverage=1.0)
                elif stype == "vol_scaled":
                    return VolScaledCSStrategy(name=f"vol_scaled_{k}", factor_weights=w_prev,
                                               top_n=tn, bottom_n=bn, leverage=1.0)
                elif stype == "top_factor":
                    return TopFactorStrategy(name=f"top_factor_{k}", factor_weights=w_prev,
                                             top_n=tn, bottom_n=bn, leverage=1.0)
                else:
                    return FactorCSStrategy(name=f"cs_{k}", factor_weights=w_prev,
                                            top_n=tn, bottom_n=bn, leverage=1.0)
            rep = pool.maybe_replace(factory)
            if rep.get("did_replace") or rep.get("added"):
                logger.info("pool update: %s", rep)

    # write ledger
    with open(os.path.join(out_dir, "ledger.jsonl"), "w", encoding="utf-8") as f:
        for row in ledger:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # report
    pool_scores = pool.scores()
    report_path = os.path.join(out_dir, "report.html")
    build_report(report_path, ledger, factor_tab, pool_scores, title="Factor Lab Pro Report")

    # latest symlink/dir copy (portable: create runs/latest as copy)
    latest_dir = os.path.join(runs_dir, "latest")
    os.makedirs(latest_dir, exist_ok=True)
    try:
        import shutil
        shutil.copy(report_path, os.path.join(latest_dir, "report.html"))
        shutil.copy(os.path.join(out_dir, "ledger.jsonl"), os.path.join(latest_dir, "ledger.jsonl"))
    except Exception:
        pass

    # runs index
    build_runs_index(runs_dir)

    logger.info("done: %s", report_path)

@app.command()
def search(config: str = typer.Option(..., "-c", "--config"),
           top_n: int = typer.Option(10, "--top-n"),
           seed: int = typer.Option(1, "--seed")):
    """Simple param search (random/grid hybrid). Outputs csv under runs/search_<ts>."""
    logger = setup_logger("search")
    cfg = load_cfg(config)

    import itertools, numpy as np
    rng = np.random.default_rng(seed)

    grid = {
        "optimizer.lam_risk": [1.0, 2.0, 3.0, 5.0],
        "optimizer.lam_l1":   [0.02, 0.05, 0.08, 0.12],
        "optimizer.lam_tc":   [0.05, 0.10, 0.15, 0.25],
        "backtest.top_n":     [2,3,4],
        "backtest.bottom_n":  [2,3,4],
    }
    keys = list(grid.keys())
    all_combo = list(itertools.product(*[grid[k] for k in keys]))
    rng.shuffle(all_combo)

    runs_dir = os.getenv("FACTOR_LAB_RUNS_DIR", cfg.report.out_dir)
    out = os.path.join(runs_dir, f"search_{ts_now_str()}.csv")

    rows=[]
    for i, vals in enumerate(all_combo[:top_n]):
        # patch cfg in-memory
        for k, v in zip(keys, vals):
            sec, name = k.split(".", 1)
            setattr(getattr(cfg, sec), name, v)

        # run a short backtest for scoring
        all_sym = load_all_sym_data(cfg)
        panel, reg = build_panel(all_sym, base_tf=cfg.backtest.base_tf, fwd_period=cfg.backtest.fwd_period, index_mode=cfg.backtest.index_mode)
        factor_names = [c for c in reg.names() if c in panel.columns]
        mined = mine_factors(panel, factor_names, cfg.mining, cfg.research, label_col="label_fwd")
        valid = mined.valid_factors or factor_names

        opt = FactorWeightOptimizer()
        w_prev = pd.Series(0.0, index=valid)

        exec_sim = ExecutionSimulator(cfg.backtest.fee_rate, cfg.backtest.slippage, cfg.execution.impact_c, cfg.execution.impact_p, cfg.execution.n_slices)
        bt = BacktestEngine(panel, base_tf=cfg.backtest.base_tf, fwd_period=cfg.backtest.fwd_period, capital=cfg.backtest.capital, exec_sim=exec_sim)

        times = panel.index.get_level_values(0).unique()
        syms = panel.index.get_level_values(1).unique()

        eq0 = bt.equity
        for t in times[: min(800, len(times))]:
            g = panel.xs(t, level=0).reindex(syms)
            X = g[valid].astype(float)
            Z = (X-X.mean())/(X.std()+1e-9)
            Z = Z.replace([float("inf"), float("-inf")], 0.0).fillna(0.0)
            if cfg.research.use_orthogonal:
                Z = orthogonalize(Z)
            r = g["label_fwd"].astype(float).replace([float("inf"), float("-inf")], 0.0).fillna(0.0)
            prem = ridge_premia(Z, r, ridge=1e-3).reindex(valid).fillna(0.0)
            Sigma = pd.DataFrame(shrink_cov((Z.values.T@Z.values)/max(1,Z.shape[0]), alpha=0.10), index=valid, columns=valid)
            w_fac, _ = opt.solve(prem, Sigma, w_prev, cfg.optimizer)
            w_prev = w_fac.reindex(valid).fillna(0.0)

            # simple cs signal
            # score = sum w*zscore
            score = pd.Series(0.0, index=syms)
            for f, w in w_prev.items():
                if f in g.columns:
                    x = g[f].astype(float)
                    z = (x-x.mean())/(x.std()+1e-9)
                    score += float(w)*z
            s = score.dropna()
            w_target = pd.Series(0.0, index=syms)
            if len(s) >= cfg.backtest.top_n + cfg.backtest.bottom_n:
                longs = s.nlargest(cfg.backtest.top_n).index
                shorts= s.nsmallest(cfg.backtest.bottom_n).index
                w_target.loc[longs] = +0.5/cfg.backtest.top_n
                w_target.loc[shorts]= -0.5/cfg.backtest.bottom_n
            bt.step(t, w_target)

        eq1 = bt.equity
        rows.append({**{k:v for k,v in zip(keys, vals)}, "equity": eq1, "return": eq1-1.0})
        logger.info("trial %d/%d equity=%.4f", i+1, top_n, eq1)

    df = pd.DataFrame(rows).sort_values("equity", ascending=False)
    df.to_csv(out, index=False)
    logger.info("search results saved: %s", out)
