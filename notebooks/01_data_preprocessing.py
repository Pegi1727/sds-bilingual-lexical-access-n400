"""
01_data_preprocessing.py
========================
Loads 'workbook (2).xlsx', validates and cleans the longitudinal dataset
(40 participants x 3 measurement months: M1, M3, M6), computes change
scores (Delta = M6 - M1) for every outcome, and exports tidy clean CSVs.

Outputs
-------
outputs/01_clean_long.csv    : tidy long-format clean data
outputs/01_change_scores.csv : one row per participant with Delta scores
"""
import argparse
import pandas as pd
import numpy as np
from scipy import stats

RAW = "workbook (2).xlsx"
OUTDIR = "outputs"
VARS = ["L1_Req", "L1_Calque", "Latency", "Fluency", "N400_Amp"]


def load_raw(path=RAW):
    """Load and return the raw workbook as a DataFrame."""
    df = pd.read_excel(path)
    return df


def validate(df):
    """Validate structure, completeness and range of the raw data."""
    need = ["ID", "Group", "Month"] + VARS
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    if df.isna().sum().sum() > 0:
        raise ValueError("Data contains missing values")
    if not set(df["Month"].unique()) == {1, 3, 6}:
        raise ValueError("Unexpected Month values")
    # Outlier screen on N400 amplitude (microvolts)
    z = np.abs(stats.zscore(df["N400_Amp"]))
    n_out = int((z > 3).sum())
    print(f"[validate] rows={len(df)} ids={df['ID'].nunique()} "
          f"groups={sorted(df['Group'].unique())} outliers(|z|>3)={n_out}")
    return df


def clean(df):
    """Basic cleaning: types, sorted order, deduplication."""
    df = df.copy()
    df["ID"] = df["ID"].astype(int)
    df["Month"] = df["Month"].astype(int)
    df["Group"] = df["Group"].str.strip()
    df = df.drop_duplicates(subset=["ID", "Month"]).sort_values(["ID", "Month"])
    return df.reset_index(drop=True)


def change_scores(df):
    """Compute Delta = M6 - M1 change scores per participant."""
    wide = df.pivot(index="ID", columns="Month", values=VARS)
    out = pd.DataFrame(index=wide.index)
    for v in VARS:
        out[f"D_{v}"] = wide[(v, 6)] - wide[(v, 1)]
    out["Group"] = df.drop_duplicates("ID").set_index("ID")["Group"]
    return out.reset_index()


def main():
    ap = argparse.ArgumentParser(description="Preprocess workbook (2).xlsx")
    ap.add_argument("--raw", default=RAW)
    a = ap.parse_args()
    df = clean(validate(load_raw(a.raw)))
    cs = change_scores(df)
    import os; os.makedirs(OUTDIR, exist_ok=True)
    df.to_csv(f"{OUTDIR}/01_clean_long.csv", index=False)
    cs.to_csv(f"{OUTDIR}/01_change_scores.csv", index=False)
    print("[done] exports: 01_clean_long.csv, 01_change_scores.csv")
    print(cs.groupby("Group").mean(numeric_only=True).round(3).to_string())


if __name__ == "__main__":
    main()
