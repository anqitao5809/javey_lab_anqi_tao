import pandas as pd
import numpy as np
import re
import os

def calculate_net_change_with_gradient(file_path):
    try:
        # 1. Improved Extraction Logic
        # We look specifically for the "BottomX-Y-ZTop" pattern 
        # to ensure we don't grab numbers from the date (like 2026-02-27).
        file_name = os.path.basename(file_path)
        match = re.search(r'Bottom\d+-(\d+)-\d+Top', file_name)
        
        if not match:
            # Fallback: Just look for the last set of hyphens if "Bottom/Top" isn't exact
            match = re.search(r'-(\d+)-\d+\D*\.csv$', file_name)

        if not match:
            print(f"Error: Could not find distance pattern in {file_name}")
            return
        
        distance_mm = float(match.group(1))
        distance_m = distance_mm / 1000.0  # Convert mm to meters

        # 2. Load and Clean Data
        df = pd.read_csv(file_path, header=None, usecols=[0, 8])
        df[0] = pd.to_numeric(df[0], errors='coerce')
        df[8] = pd.to_numeric(df[8], errors='coerce')
        df = df.dropna().reset_index(drop=True)

        # --- PART A: PRE-SURGE BASELINE (5 MINS) ---
        window_size_5 = 600
        surge_threshold = df[8].max() * 0.20
        surge_start_idx = (df[8] > surge_threshold).idxmax()
        
        pre_surge_df = df.iloc[:surge_start_idx].copy()
        if len(pre_surge_df) < window_size_5:
            best_base_end = window_size_5
        else:
            rolling_std_base = pre_surge_df[8].rolling(window=window_size_5).std()
            best_base_end = rolling_std_base.idxmin()
        
        avg_baseline = df[8].iloc[best_base_end - window_size_5 : best_base_end].mean()

        # --- PART B: PRIORITY PLATEAU (10 MINS) ---
        window_size_10 = 1200
        rolling_mean = df[8].rolling(window=window_size_10).mean()
        rolling_std = df[8].rolling(window=window_size_10).std()

        max_possible_mean = rolling_mean.max()
        high_value_threshold = max_possible_mean * 0.95
        high_value_indices = rolling_mean[rolling_mean >= high_value_threshold].index
        best_plat_end = rolling_std[high_value_indices].idxmin()
        
        avg_plateau = df[8].iloc[best_plat_end - window_size_10 : best_plat_end].mean()

        # --- PART C: FINAL CALCULATIONS ---
        net_difference = avg_plateau - avg_baseline
        humidity_gradient = net_difference / distance_m

        print("-" * 60)
        print(f"FILE:            {file_name}")
        print(f"EXTRACTED DIST:  {distance_mm} mm -> {distance_m:.4f} meters")
        print(f"AVG BASELINE:    {avg_baseline:.6f} g/m³")
        print(f"AVG PLATEAU:     {avg_plateau:.6f} g/m³")
        print(f"NET CHANGE (ΔC): {net_difference:.6f} g/m³")
        print(f"GRADIENT (ΔC/d): {humidity_gradient:.6f} g/m⁴")
        print("-" * 60)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    # This should now correctly ignore "02-27" and find "4"
    filename = "log_only_2026-02-27_09-12-16 Bottom8-4-8Top.csv"
    calculate_net_change_with_gradient(filename)