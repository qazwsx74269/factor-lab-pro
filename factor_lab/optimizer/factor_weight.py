from __future__ import annotations
import numpy as np
import pandas as pd
import cvxpy as cp

def shrink_cov(C: np.ndarray, alpha=0.10):
    D = np.diag(np.diag(C))
    return (1-alpha)*C + alpha*D

def orthogonalize(Z: pd.DataFrame) -> pd.DataFrame:
    X = Z.values.astype(float)
    N, K = X.shape
    Q = np.zeros_like(X)
    for j in range(K):
        v = X[:,j].copy()
        for i in range(j):
            qi = Q[:,i]
            denom = float(qi@qi)
            if denom > 1e-12:
                v -= (v@qi)/denom*qi
        Q[:,j] = v
    return pd.DataFrame(Q, index=Z.index, columns=Z.columns)

def ridge_premia(Z: pd.DataFrame, r: pd.Series, ridge=1e-3) -> pd.Series:
    idx = Z.index.intersection(r.index)
    X = Z.reindex(idx).values.astype(float)
    y = r.reindex(idx).values.astype(float)
    m = np.isfinite(X).all(axis=1) & np.isfinite(y)
    X = X[m]; y = y[m]
    if len(y) < max(8, Z.shape[1]*2):
        return pd.Series(0.0, index=Z.columns)
    XtX = X.T @ X
    K = XtX.shape[0]
    XtX.flat[::K+1] += ridge
    f = np.linalg.solve(XtX, X.T @ y)
    return pd.Series(f, index=Z.columns)

class FactorWeightOptimizer:
    def __init__(self, solver="OSQP"):
        self.solver = solver

    def solve(self, mu: pd.Series, Sigma: pd.DataFrame, w_prev: pd.Series, cfg_opt):
        facs = list(mu.index)
        if len(facs)==0:
            return pd.Series(dtype=float), {"status":"empty"}
        m = mu.values.astype(float)
        S = Sigma.reindex(index=facs, columns=facs).fillna(0.0).values.astype(float)
        S = 0.5*(S+S.T)
        S[np.diag_indices_from(S)] += 1e-8
        wp = w_prev.reindex(facs).fillna(0.0).values.astype(float)

        w = cp.Variable(len(facs))
        obj = cp.Maximize(
            m@w
            - float(cfg_opt.lam_risk) * cp.quad_form(w, S)
            - float(cfg_opt.lam_l1)  * cp.norm1(w)
            - float(cfg_opt.lam_tc)  * cp.norm1(w-wp)
        )
        cons = [
            cp.norm1(w) <= float(cfg_opt.l1_cap),
            cp.abs(w) <= float(cfg_opt.w_max),
        ]
        prob = cp.Problem(obj, cons)
        try:
            prob.solve(solver=getattr(cp, self.solver), warm_start=True)
        except Exception:
            prob.solve(solver=cp.SCS)
        if w.value is None:
            return pd.Series(0.0, index=facs), {"status":"fail"}
        out = pd.Series(np.asarray(w.value).astype(float), index=facs)
        out = out / (out.abs().sum() + 1e-12)
        return out.sort_values(key=lambda s: s.abs(), ascending=False), {"status":"ok", "obj": float(prob.value) if prob.value is not None else None}
