"""
scripts/plot_erp_trajectory.py
==============================
Extracts representative subject scalars from MATLAB .mat files
and plots publication-grade longitudinal ERP trajectory (EG vs CG).

Usage:
    python scripts/plot_erp_trajectory.py
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.io import loadmat


def load_representative_mat_files(data_dir):
    """
    Reads and validates all .mat files in the representative samples directory.
    """
    pattern = os.path.join(data_dir, "sub-*_M*.mat")
    mat_files = sorted(glob.glob(pattern))
    
    if not mat_files:
        raise FileNotFoundError(f"No .mat files found in: {data_dir}")
        
    records = []
    for filepath in mat_files:
        mat_data = loadmat(filepath)
        
        # Extract scalar keys
        sub_id = int(mat_data['subject_id'][0][0])
        group = str(mat_data['group'][0])
        month = int(mat_data['month'][0][0])
        amp = float(mat_data['n400_amplitude_uv'][0][0])
        status = str(mat_data['status'][0])
        
        records.append({
            'subject_id': sub_id,
            'group': group,
            'month': month,
            'n400_amp': amp,
            'status': status,
            'label': f"Sub-{sub_id:02d} ({group})"
        })
        
    return pd.DataFrame(records)


def plot_trajectory(df, output_path):
    """
    Generates and saves a publication-ready lineplot.
    """
    plt.figure(figsize=(7.5, 4.8), dpi=300)
    sns.set_theme(style="ticks", font="sans-serif")
    
    palette = {'Sub-01 (EG)': '#1f77b4', 'Sub-21 (CG)': '#d62728'}
    markers = {'Sub-01 (EG)': 'o', 'Sub-21 (CG)': 's'}
    
    ax = sns.lineplot(
        data=df,
        x='month',
        y='n400_amp',
        hue='label',
        style='label',
        palette=palette,
        markers=markers,
        dashes=False,
        linewidth=2.2,
        markersize=8
    )
    
    # Add numerical labels on data points
    for _, row in df.iterrows():
        offset = 0.22 if row['group'] == 'EG' else -0.25
        ax.text(
            row['month'], 
            row['n400_amp'] + offset,
            f"{row['n400_amp']:.2f} μV",
            ha='center', 
            va='center',
            fontsize=8.5,
            fontweight='bold',
            color='#333333'
        )
    
    plt.title("Longitudinal N400 Attenuation (Representative Single Subjects)", fontsize=12, fontweight='bold', pad=14)
    plt.xlabel("Assessment Timepoint", fontsize=11, fontweight='semibold')
    plt.ylabel("Extracted N400 Amplitude (μV)", fontsize=11, fontweight='semibold')
    
    plt.xticks([1, 3, 6], ['Month 1 (Baseline)', 'Month 3 (Mid-test)', 'Month 6 (Post-test)'])
    plt.ylim(-6.5, -0.5)
    
    sns.despine(top=True, right=True)
    plt.legend(title='Representative Subject', title_fontsize='10', fontsize='9', loc='lower right', frameon=True)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[OK] Publication figure saved to: {output_path}")


def main():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, '..', 'data', 'representative_samples')
    fig_path = os.path.join(base_dir, '..', 'figures', 'representative_subjects_trajectory.png')
    
    print(f"Reading sample files from: {data_dir}")
    df = load_representative_mat_files(data_dir)
    print("Extracted Data Table:")
    print(df[['subject_id', 'group', 'month', 'n400_amp', 'status']])
    
    plot_trajectory(df, fig_path)


if __name__ == '__main__':
    main()
