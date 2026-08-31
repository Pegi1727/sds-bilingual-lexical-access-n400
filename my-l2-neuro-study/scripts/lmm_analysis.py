"""
scripts/lmm_analysis.py
========================
Longitudinal Linear Mixed-Effects Model (LMM) Analysis
for N400 ERP Attenuation across 6-Month Intervention.

Usage:
    python scripts/lmm_analysis.py
"""

import os
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def generate_cohort_metadata(n_subjects=40, seed=42):
    """
    Generates synthetic longitudinal ERP metadata (N=40, 3 timepoints)
    consistent with study parameters.
    """
    np.random.seed(seed)
    records = []
    
    for sub_id in range(1, n_subjects + 1):
        group = 'EG' if sub_id <= (n_subjects // 2) else 'CG'
        
        if group == 'EG':
            m1 = -5.32 + np.random.normal(0, 0.35)
            m3 = -3.45 + np.random.normal(0, 0.30)
            m6 = -1.60 + np.random.normal(0, 0.25)
        else:
            m1 = -5.41 + np.random.normal(0, 0.35)
            m3 = -5.12 + np.random.normal(0, 0.30)
            m6 = -4.85 + np.random.normal(0, 0.25)
            
        records.extend([
            {'ID': sub_id, 'Group': group, 'Month': 1, 'N400_Amp': m1},
            {'ID': sub_id, 'Group': group, 'Month': 3, 'N400_Amp': m3},
            {'ID': sub_id, 'Group': group, 'Month': 6, 'N400_Amp': m6}
        ])
        
    return pd.DataFrame(records)


def fit_lmm(df, formula="N400_Amp ~ C(Group, Treatment('CG')) * Month"):
    """
    Fits Linear Mixed-Effects Model with random intercept per participant.
    """
    print("Fitting Linear Mixed-Effects Model...")
    print(f"Formula: {formula}")
    model = smf.mixedlm(formula, df, groups=df["ID"])
    result = model.fit()
    return result


def main():
    # 1. Dataset preparation
    df = generate_cohort_metadata()
    print(f"Data summary: {len(df)} total observations across {df['ID'].nunique()} subjects.")
    
    # 2. Fit model
    lmm_res = fit_lmm(df)
    print("\n" + "=" * 60)
    print("LMM STATISTICAL RESULTS SUMMARY")
    print("=" * 60)
    print(lmm_res.summary())
    
    # 3. Save output
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'docs')
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, 'lmm_results.txt')
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(lmm_res.summary().as_text())
        
    print(f"\n[OK] LMM results successfully saved to: {out_path}")


if __name__ == '__main__':
    main()
