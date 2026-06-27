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

        # --- ROBUST BASELINE LOGIC ---
        window_5 = 600
        surge_threshold = df_c[8].max() * 0.20
        # Find first index where humidity exceeds 20% of max
        is_above_threshold = df_c[8] > surge_threshold
        if not is_above_threshold.any():
            surge_start_idx = len(df_c) - 1
        else:
            surge_start_idx = is_above_threshold.idxmax()

        # Define search area: 10 minutes before the surge
        search_start = max(0, surge_start_idx - 1200)
        pre_surge_zone = df_c.iloc[search_start:surge_start_idx]

        if len(pre_surge_zone) < window_5:
            # Fallback if surge happens too early
            avg_baseline = df_c[8].iloc[0:min(window_5, len(df_c))].mean()
        else:
            # Calculate rolling std and find the flattest window
            rolling_std = pre_surge_zone[8].rolling(window=window_5).std().dropna()
            
            if rolling_std.empty:
                # Manual fallback if rolling fails
                avg_baseline = df_c[8].iloc[surge_start_idx - window_5 : surge_start_idx].mean()
            else:
                best_end_idx = rolling_std.idxmin()
                avg_baseline = df_c[8].iloc[int(best_end_idx - window_5 + 1) : int(best_end_idx + 1)].mean()

        # --- PLATEAU (10 MINS) ---
        window_10 = 1200
        rolling_mean = df_c[8].rolling(window=window_10).mean()
        rolling_std_plat = df_c[8].rolling(window=window_10).std()
        
        max_mean = rolling_mean.max()
        high_val_indices = rolling_mean[rolling_mean >= max_mean * 0.95].index
        
        if high_val_indices.empty:
            best_plat_end = rolling_mean.idxmax()
        else:
            best_plat_end = rolling_std_plat[high_val_indices].idxmin()
        
        t_start = df_c['minutes'].iloc[int(best_plat_end - window_10 + 1)]
        t_end = df_c['minutes'].iloc[int(best_plat_end)]
        avg_plateau = df_c[8].iloc[int(best_plat_end - window_10 + 1) : int(best_plat_end + 1)].mean()

        # 4. Process Excel Data (Weight)
        df_w = pd.read_excel(xlsx_path, header=None)
        df_w[0] = pd.to_datetime(df_w[0], format='%b-%d-%Y %I:%M %p')
        df_w['offset'] = df_w.groupby(0).cumcount() * 10 
        w_start_time = df_w[0].iloc[0]
        df_w['minutes'] = ((df_w[0] - w_start_time).dt.total_seconds() + df_w['offset']) / 60.0

        mask = (df_w['minutes'] >= t_start) & (df_w['minutes'] <= t_end)
        df_w_segment = df_w[mask]
        
        if len(df_w_segment) < 2:
            print(f"Error: Not enough weight data in window {t_start:.2f}-{t_end:.2f}")
            return

        slope_min, intercept, r_val, _, _ = linregress(df_w_segment['minutes'], df_w_segment.iloc[:, 1])
        
        # 5. Final Calculations
        abs_diff_humidity = avg_plateau - avg_baseline
        humidity_gradient = abs_diff_humidity / distance_m
        
        #slope_sec = slope_min / 60.0
        slope_sec = -0.0065457168
        area_m2 = 0.01 * 0.01 
        weight_flux_sec = slope_sec / area_m2
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
    # Point to the specific problematic folder
    target_folder = r"C:\Users\taq58\Desktop\bsac\Previous data\Bottom12-8-8Top" 
    calculate_folder_metrics(target_folder)