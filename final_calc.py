import pandas as pd
import numpy as np
import re
import os
import glob
from scipy.stats import linregress

def calculate_folder_metrics(folder_path):
    try:
        # 1. Locate Files
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        xlsx_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
        
        if not csv_files or not xlsx_files:
            print(f"Error: Missing files in {folder_path}")
            return

        csv_path = csv_files[0]
        xlsx_path = xlsx_files[0]
        file_name = os.path.basename(csv_path)

        # 2. Extract Distance from Filename
        match = re.search(r'Bottom\d+-(\d+)-\d+Top', file_name)
        if not match:
            match = re.search(r'-(\d+)-\d+\D*\.csv$', file_name)
        
        if not match:
            print(f"Error: Could not find distance pattern in {file_name}")
            return
        
        distance_mm = float(match.group(1))
        distance_m = distance_mm / 1000.0

        # 3. Process CSV Data (Humidity)
        df_c = pd.read_csv(csv_path, header=None, usecols=[0, 8])
        df_c[0] = pd.to_numeric(df_c[0], errors='coerce')
        df_c[8] = pd.to_numeric(df_c[8], errors='coerce')
        df_c = df_c.dropna().reset_index(drop=True)

        c_start_unix = df_c[0].iloc[0]
        df_c['minutes'] = (df_c[0] - c_start_unix) / 60.0

        # --- BASELINE (5 MINS) ---
        window_5 = 600
        surge_threshold = df_c[8].max() * 0.20
        surge_start_idx = (df_c[8] > surge_threshold).idxmax()
        pre_surge_df = df_c.iloc[:surge_start_idx].copy()
        
        if len(pre_surge_df) < window_5:
            best_base_end = window_5
        else:
            rolling_std_base = pre_surge_df[8].rolling(window=window_5).std()
            best_base_end = rolling_std_base.idxmin()
        
        avg_baseline = df_c[8].iloc[best_base_end - window_5 : best_base_end].mean()

        # --- PLATEAU (10 MINS) ---
        window_10 = 1200
        rolling_mean = df_c[8].rolling(window=window_10).mean()
        rolling_std = df_c[8].rolling(window=window_10).std()
        
        max_mean = rolling_mean.max()
        high_val_indices = rolling_mean[rolling_mean >= max_mean * 0.95].index
        best_plat_end = rolling_std[high_val_indices].idxmin()
        
        t_start = df_c['minutes'].iloc[best_plat_end - window_10 + 1]
        t_end = df_c['minutes'].iloc[best_plat_end]
        avg_plateau = df_c[8].iloc[best_plat_end - window_10 : best_plat_end].mean()

        # 4. Process Excel Data (Weight)
        df_w = pd.read_excel(xlsx_path, header=None)
        df_w[0] = pd.to_datetime(df_w[0], format='%b-%d-%Y %I:%M %p')
        df_w['offset'] = df_w.groupby(0).cumcount() * 10 
        w_start_time = df_w[0].iloc[0]
        df_w['minutes'] = ((df_w[0] - w_start_time).dt.total_seconds() + df_w['offset']) / 60.0

        mask = (df_w['minutes'] >= t_start) & (df_w['minutes'] <= t_end)
        df_w_segment = df_w[mask]
        
        slope_min, intercept, r_val, _, _ = linregress(df_w_segment['minutes'], df_w_segment.iloc[:, 1])
        
        # 5. Final Calculations
        abs_diff_humidity = avg_plateau - avg_baseline
        humidity_gradient = abs_diff_humidity / distance_m
        
        slope_sec = slope_min / 60.0
        area_m2 = 0.01 * 0.01 # 1cm x 1cm
        weight_flux_sec = slope_sec / area_m2

        # --- DIFFUSION COEFFICIENT ---
        # D = - (Flux / Gradient)
        # We negate it because flux is leaving the sample (negative slope)
        diffusion_coeff = -(weight_flux_sec / humidity_gradient)

        # 6. Terminal Output
        print("-" * 65)
        print(f"FOLDER:          {os.path.basename(folder_path)}")
        print(f"DISTANCE:        {distance_m:.4f} m")
        print(f"TIME WINDOW:     {t_start:.2f} to {t_end:.2f} min")
        print(f"AVG BASELINE:    {avg_baseline:.6f} g/m³")
        print(f"AVG PLATEAU:     {avg_plateau:.6f} g/m³")
        print(f"ABS DIFF (ΔC):   {abs_diff_humidity:.6f} g/m³")
        print(f"HUMIDITY GRAD:   {humidity_gradient:.6f} g/m⁴")
        print(f"WEIGHT SLOPE:    {slope_sec:.10f} g/s")
        print(f"WEIGHT FLUX:     {weight_flux_sec:.8f} g/(m²·s)")
        print(f"R-SQUARED:       {r_val**2:.4f}")
        print(f"DIFFUSION COEFF: {diffusion_coeff:.10f} m²/s")
        print("-" * 65)

    except Exception as e:
        print(f"Error processing folder {folder_path}: {e}")

if __name__ == "__main__":
    target_folder = r"C:\Users\taq58\Desktop\bsac\Previous data\Bottom8-8-12Top" 
    calculate_folder_metrics(target_folder)