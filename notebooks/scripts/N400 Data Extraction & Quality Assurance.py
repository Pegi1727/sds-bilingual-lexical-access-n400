import numpy as np
import pandas as pd

def extract_n400_roi(df, roi_channels=['Cz', 'Pz', 'CP1', 'CP2'], t_min=300, t_max=500):
    """
    Extracts mean N400 amplitude within a specified Region of Interest (ROI)
    and time window (default: 300-500 ms post-stimulus onset).
    
    Parameters:
        df (pd.DataFrame): Epoch-level or participant-level ERP table.
                           Expected columns: 'Channel', 'Time_ms', 'Voltage_uV', 'Subject_ID'
    Returns:
        pd.DataFrame: Aggregated N400 mean amplitude per subject/condition.
    """
    # 1. فیلتر کردن بر اساس پنجره زمانی و الکترودهای هدف
    mask = (df['Time_ms'] >= t_min) & (df['Time_ms'] <= t_max) & (df['Channel'].isin(roi_channels))
    filtered_df = df[mask]
    
    # 2. محاسبه میانگین ولتاژ برای هر آزمودنی در شرایط مختلف
    n400_df = (
        filtered_df.groupby(['Subject_ID', 'Group', 'Condition'])['Voltage_uV']
        .mean()
        .reset_index()
        .rename(columns={'Voltage_uV': 'N400_mean_amplitude'})
    )
    
    # 3. چک کردن خودکار مقادیر پرت (Outlier/Artifact Alert: e.g. > ±30 µV)
    outliers = n400_df[n400_df['N400_mean_amplitude'].abs() > 30]
    if not outliers.empty:
        print(f"[Warning] Potential residual artifacts detected in {len(outliers)} instances.")
        
    return n400_df

