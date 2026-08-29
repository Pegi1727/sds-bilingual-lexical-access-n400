"""
03_statistical_models.py
========================
Fits the confirmatory statistical models of the study:
  * Poisson GEE for L1_Req and L1_Calque (count outcomes, exchangeable corr.),
  * Linear Mixed Models for Latency, Fluency and N400_Amp,
and exports a complete model summary table.

Output
------
outputs/02_gee_lmm_results.csv : term, estimate, SE, z/t, p, CI, AIC/QIC
"""
import argparse
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

CLEAN = "outputs/01_clean_long.csv"
OUTDIR = "outputs"
FORMULAS = {
    ("Poisson GEE", "L1_Req"):   "L1_Req ~ Month_c * EG",
    ("Poisson GEE", "L1_Calque"):"L1_Calque ~ Month_c * EG",
    ("LMM", "Latency"): "Latency ~ Month_c * EG",
    ("LMM", "Fluency"): "Fluency ~ Month_c * EG",
    ("LMM", "N400_Amp"):"N400_Amp ~ Month_c * EG",
}


def prep(df):
    df = df.copy()
    df["Month_c"] = df["Month"] - 1
    df["EG"] = (df["Group"] == "EG").astype(int)
    return df


def extract_gee(model, label, outcome):
    rows = []
    for name, est in model.params.items():
        se = model.bse[name]
        z = est / se
        p = model.pvalues[name]
        rows.append({"Model": label, "Outcome": outcome, "Term": name,
                     "Estimate": round(est, 4), "SE": round(se, 4),
                     "z/t": round(z, 3), "p": round(p, 4),
                     "CI_low": round(est - 1.96 * se, 4),
                     "CI_high": round(est + 1.96 * se, 4),
                     "Wald_Chi2": round(model.wald_test_terms().statistic.max(), 2)
                     if name == "Group Var" else np.nan,
                     "AIC": np.nan, "QIC": round(model.qic()[0], 2)})
    return rows


def extract_lmm(model, label, outcome):
    rows = []
    params = model.params
    bse = model.bse
    tvals = model.tvalues
    pvals = model.pvalues
    ci = model.conf_int()
    for name in params.index:
        rows.append({"Model": label, "Outcome": outcome, "Term": name,
                     "Estimate": round(params[name], 4), "SE": round(bse[name], 4),
                     "z/t": round(tvals[name], 3), "p": round(pvals[name], 4),
                     "CI_low": round(ci.loc[name, 0], 4),
                     "CI_high": round(ci.loc[name, 1], 4),
                     "Wald_Chi2": np.nan,
                     "AIC": round(model.aic, 2), "QIC": np.nan})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=CLEAN)
    a = ap.parse_args()
    df = prep(pd.read_csv(a.data))
    rows = []
    for (label, outcome), f in FORMULAS.items():
        if label == "Poisson GEE":
            m = smf.gee(f, "ID", df, family=sm.families.Poisson(),
                        cov_struct=sm.cov_struct.Exchangeable()).fit()
            rows += extract_gee(m, label, outcome)
        else:
            m = smf.mixedlm(f, df, groups=df["ID"]).fit(reml=False)
            rows += extract_lmm(m, label, outcome)
    res = pd.DataFrame(rows)
    import os; os.makedirs(OUTDIR, exist_ok=True)
    res.to_csv(f"{OUTDIR}/02_gee_lmm_results.csv", index=False)
    print(res.to_string(index=False))
    print(f"\n[done] wrote {OUTDIR}/02_gee_lmm_results.csv ({len(res)} rows)")


if __name__ == "__main__":
    main()
