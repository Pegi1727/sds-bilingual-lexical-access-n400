"""
04_path_model.py
================
Mediation / structural path analysis:
    Group (EG=1) -> Delta N400 (mediator) -> Delta outcomes (Latency, Fluency,
    L1_Req, L1_Calque)
Indirect (mediated) effects tested with 5000-iteration bootstrap CIs.

Output
------
outputs/04_path_model.csv : paths a, b, c', indirect effect, boot 95% CI, p
"""
import argparse
import numpy as np
import pandas as pd

CLEAN = "outputs/01_change_scores.csv"
OUTDIR = "outputs"
N_BOOT = 5000
MEDIATOR = "D_N400_Amp"
OUTCOMES = ["D_Latency", "D_Fluency", "D_L1_Req", "D_L1_Calque"]


def ols_path(X, y):
    """Return slope of simple OLS regression y ~ X (with intercept)."""
    X1 = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return beta[1]


def bootstrap_indirect(eg, m, y, n_boot=N_BOOT, seed=42):
    """Bootstrap the indirect effect a*b and direct path c'."""
    rng = np.random.default_rng(seed)
    n = len(eg)
    ind, dirs = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        a = ols_path(eg[idx], m[idx])
        b = ols_path(m[idx], y[idx])
        cp = ols_path(np.column_stack([eg[idx], m[idx]]), y[idx])
        ind.append(a * b)
        dirs.append(cp)
    return np.array(ind), np.array(dirs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=CLEAN)
    ap.add_argument("--nboot", type=int, default=N_BOOT)
    a = ap.parse_args()
    df = pd.read_csv(a.data)
    eg = (df["Group"] == "EG").astype(int).to_numpy(float)
    med = df[MEDIATOR].to_numpy(float)
    rows = []
    for out in OUTCOMES:
        y = df[out].to_numpy(float)
        a_path = ols_path(eg, med)
        b_path = ols_path(med, y)
        c_total = ols_path(eg, y)
        cp = ols_path(np.column_stack([eg, med]), y)
        boot_ind, _ = bootstrap_indirect(eg, med, y, a.nboot, seed=42 + hash(out) % 100)
        lo, hi = np.percentile(boot_ind, [2.5, 97.5])
        p_ind = 2 * min((boot_ind <= 0).mean(), (boot_ind >= 0).mean())
        rows.append({"Outcome": out, "a_path": round(a_path, 4),
                     "b_path": round(b_path, 4), "c_total": round(c_total, 4),
                     "c_prime": round(cp, 4),
                     "indirect_ab": round(a_path * b_path, 4),
                     "boot_CI_low": round(lo, 4), "boot_CI_high": round(hi, 4),
                     "boot_p": round(p_ind, 4),
                     "mediated_pct": round(100 * a_path * b_path / c_total, 1)
                     if c_total != 0 else np.nan})
    res = pd.DataFrame(rows)
    import os; os.makedirs(OUTDIR, exist_ok=True)
    res.to_csv(f"{OUTDIR}/04_path_model.csv", index=False)
    print(res.to_string(index=False))
    print(f"[done] wrote {OUTDIR}/04_path_model.csv (boot n={a.nboot})")


if __name__ == "__main__":
    main()
