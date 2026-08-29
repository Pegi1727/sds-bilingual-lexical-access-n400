"""
02_erp_n400_analysis.py
=======================
Longitudinal ERP / N400 analysis:
  * within-subject extraction of N400 peak and mean amplitudes per month,
  * repeated-measures effect sizes (Cohen's d for paired samples),
  * GEE and Linear Mixed Model (LMM) of N400 amplitude ~ Month * Group.

Outputs
-------
outputs/02_n400_summary.csv : per-group per-month descriptive stats + Cohen's d
outputs/02_n400_models.txt  : GEE and LMM text summaries
"""
import argparse
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

CLEAN = "outputs/01_clean_long.csv"
OUTDIR = "outputs"


def cohens_d_paired(a, b):
    """Cohen's d for paired samples (dz)."""
    d = np.asarray(a, float) - np.asarray(b, float)
    return d.mean() / d.std(ddof=1)


def peak_mean_amplitudes(df):
    """Extract peak (most-negative) and mean amplitude summaries per group/month."""
    g = (df.groupby(["Group", "Month"])["N400_Amp"]
           .agg(N="count", Mean="mean", SD="std",
                Peak_Min="min").round(3).reset_index())
    return g


def fit_models(df):
    """Fit GEE and LMM for N400_Amp ~ Month * Group with subject random effect."""
    df = df.copy()
    df["Month_c"] = df["Month"] - df["Month"].min()
    df["EG"] = (df["Group"] == "EG").astype(int)
    res = {}
    gee = smf.gee("N400_Amp ~ Month_c * EG", "ID", df,
                  family=sm.families.Gaussian(),
                  cov_struct=sm.cov_struct.Exchangeable()).fit()
    lmm = smf.mixedlm("N400_Amp ~ Month_c * EG", df, groups=df["ID"]).fit(reml=False)
    res["gee"], res["lmm"] = gee, lmm
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=CLEAN)
    a = ap.parse_args()
    df = pd.read_csv(a.data)
    summ = peak_mean_amplitudes(df)
    # Paired Cohen's d M1 -> M6 per group
    rows = []
    for grp, sub in df.groupby("Group"):
        w = sub.pivot(index="ID", columns="Month", values="N400_Amp")
        rows.append({"Group": grp, "d_M1_M6": round(cohens_d_paired(w[6], w[1]), 3)})
    dtab = pd.DataFrame(rows)
    summ = summ.merge(dtab, on="Group", how="left")
    res = fit_models(df)
    import os; os.makedirs(OUTDIR, exist_ok=True)
    summ.to_csv(f"{OUTDIR}/02_n400_summary.csv", index=False)
    with open(f"{OUTDIR}/02_n400_models.txt", "w") as f:
        f.write("=== GEE: N400_Amp ~ Month * Group ===\n" + str(res["gee"].summary()))
        f.write("\n\n=== LMM: N400_Amp ~ Month * Group ===\n" + str(res["lmm"].summary()))
    print(summ.to_string(index=False))
    print("\nLMM fixed effects:\n", res["lmm"].params.round(4).to_string())


if __name__ == "__main__":
    main()
