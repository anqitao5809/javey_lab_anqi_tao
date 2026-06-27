import pandas as pd
import numpy as np
import re
import os
import glob
from scipy.stats import linregress

def print_slope_comparison(folder_path):
    try:
        # 1. Locate Files
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        xlsx_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
        
        if not csv_files or not xlsx_files:
            return print(f"Error: Missing files in {folder_path}")

        # 2. Process Humidity to find the "Active" Window
        df_c = pd.read_csv(csv_files[0], header=None, usecols=[0, 8])
        df_c[0] = pd.to_numeric(df_c[0], errors='coerce')
        df_c[8] = pd.to_numeric(df_c[8], errors='coerce')
        df_c = df_c.dropna().reset_index(drop=True)
        
        c_start_unix = df_c[0].iloc[0]
        df_c['minutes'] = (df_c[0] - c_start_unix) / 60.0
        
        # Detect Surge (Start of experiment)
        surge_threshold = df_c[8].max() * 0.20
        t_surge_start = df_c['minutes'].iloc[(df_c[8] > surge_threshold).idxmax()]
        
        # Detect Decline (End of experiment)
        max_idx = df_c[8].idxmax()
        post_peak_df = df_c[8].iloc[max_idx:]
        decline_threshold = df_c[8].max() * 0.90
        
        if any(post_peak_df < decline_threshold):
            t_decline_start = df_c['minutes'].iloc[(post_peak_df < decline_threshold).idxmax()]
        else:
            t_decline_start = df_c['minutes'].iloc[-1]

        # 3. Process Weight Data
        df_w = pd.read_excel(xlsx_files[0], header=None)
        df_w[0] = pd.to_datetime(df_w[0], format='%b-%d-%Y %I:%M %p')
        df_w['offset'] = df_w.groupby(0).cumcount() * 10 
        w_start_time = df_w[0].iloc[0]
        df_w['minutes'] = ((df_w[0] - w_start_time).dt.total_seconds() + df_w['offset']) / 60.0
        weight_col = df_w.columns[1]

        # 4. Calculate Segment Slopes (g/min)
        def get_slope(df_subset):
            if len(df_subset) < 2: return 0.0
            slope, _, _, _, _ = linregress(df_subset['minutes'], df_subset[weight_col])
            return slope

        slope_pre = get_slope(df_w[df_w['minutes'] < t_surge_start])
        slope_active = get_slope(df_w[(df_w['minutes'] >= t_surge_start) & (df_w['minutes'] <= t_decline_start)])
        slope_post = get_slope(df_w[df_w['minutes'] > t_decline_start])

        # 5. Output
        print("-" * 50)
        print(f"FOLDER: {os.path.basename(folder_path)}")
        print(f"Active Window: {t_surge_start:.2f} to {t_decline_start:.2f} min")
        print("-" * 50)
        print(f"1. PRE-SURGE SLOPE:  {slope_pre:.10f} g/min")
        print(f"2. ACTIVE PHASE SLOPE: {slope_active:.10f} g/min")
        print(f"3. POST-DECLINE SLOPE: {slope_post:.10f} g/min")
        print("-" * 50)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    target_folder = r"C:\Users\taq58\Desktop\bsac\Previous data\Bottom8-8-8Top" 
    print_slope_comparison(target_folder)