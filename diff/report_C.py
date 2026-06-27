import pandas as pd
from pathlib import Path
import math

def process_experiment_data(folder_path, diameter_mm=10):
    try:
        folder = Path(folder_path)
        
        # --- 1. PROCESS XLSX FILE (Weight Data) ---
        xlsx_files = list(folder.glob("*.xlsx"))
        weight_gradient_per_sec = 0
        
        if xlsx_files:
            xf = xlsx_files[0]
            df_weight = pd.read_excel(xf, header=None, usecols=[0, 1])
            df_weight = df_weight.dropna()

            df_weight[0] = pd.to_datetime(df_weight[0], format='%b-%d-%Y %I:%M %p', errors='coerce')
            df_weight[1] = pd.to_numeric(df_weight[1], errors='coerce')
            df_weight = df_weight.dropna()

            if not df_weight.empty:
                weight_start = df_weight[1].iloc[0]
                weight_end = df_weight[1].iloc[-1]
                time_start = df_weight[0].iloc[0]
                time_end = df_weight[0].iloc[-1]
                
                weight_diff_mg = weight_end - weight_start
                weight_diff_g = weight_diff_mg / 1000.0
                duration_seconds = (time_end - time_start).total_seconds()
                
                print(f"--- Weight Data ({xf.name}) ---")
                print(f"Weight Diff:      {weight_diff_g:.4f} g")
                
                if duration_seconds > 0:
                    weight_rate_per_sec = weight_diff_g / duration_seconds
                    
                    # Area in m^2
                    radius_m = (diameter_mm / 2.0) / 1000.0
                    area_m2 = math.pi * (radius_m ** 2)
                    weight_gradient_per_sec = weight_rate_per_sec / area_m2
                    
                    print(f"Duration:         {duration_seconds:.1f} seconds")
                    print(f"Weight/Second:    {weight_rate_per_sec:.8f} g/s")
                    print(f"Weight Gradient:  {weight_gradient_per_sec:.8f} g/(s·m²)")
                else:
                    print("Duration:         0 seconds.")
                print("-" * 40)
            else:
                print("Error: Excel file contained no valid data rows.")

        # --- 2. PROCESS CSV FILE (AH Data) ---
        csv_files = list(folder.glob("new*.csv"))
        if not csv_files:
            return
        
        file_path = csv_files[0]
        df = pd.read_csv(file_path, header=None, usecols=[0, 8])
        df[0] = pd.to_numeric(df[0], errors='coerce')
        df[8] = pd.to_numeric(df[8], errors='coerce')
        df = df.dropna(subset=[0, 8]).reset_index(drop=True)

        # Handle Time in Seconds (0.5s intervals)
        df['sub_second_offset'] = df.groupby(0).cumcount() * 0.5
        start_time_unix = df[0].iloc[0]
        df['elapsed_seconds'] = (df[0] - start_time_unix) + df['sub_second_offset']

        # Small Sliding Window Detection (3 min = 180 seconds = 360 rows)
        window_size = 360 
        df['window_diff'] = df[8].diff(periods=window_size)
        detection_indices = df.index[df['window_diff'] > 0.75].tolist()

        if detection_indices:
            detect_idx = detection_indices[0]
            search_start = max(0, detect_idx - window_size)
            lookback_zone = df.iloc[search_start : detect_idx]
            
            spike_start_idx = lookback_zone[8].idxmin()
            baseline_value = df.loc[spike_start_idx, 8]
            spike_start_time_sec = df.loc[spike_start_idx, 'elapsed_seconds']
            
            # Normalize and identify plateau
            df['normalized_ah'] = df[8] - baseline_value
            # Plateau at 30 minutes = 1800 seconds
            target_time_sec = spike_start_time_sec + 1800.0
            idx_30min = (df['elapsed_seconds'] - target_time_sec).abs().idxmin()
            
            if target_time_sec <= df['elapsed_seconds'].max():
                plateau_value = 2.25 #df.loc[idx_30min, 'normalized_ah']
                distance_val = 0.08
                ah_gradient = plateau_value / distance_val

                print(f"--- AH Analysis ({file_path.name}) ---")
                print(f"Spike Start:      {spike_start_time_sec:.1f} s")
                print(f"Plateau Time:     {target_time_sec:.1f} s")
                print(f"Plateau Value:    {plateau_value:.4f} g/m³")
                print(f"AH Gradient:      {ah_gradient:.4f} g/m⁴")
                print("-" * 40)

                # --- 3. FINAL CALCULATION: DIFF FACTOR ---
                if ah_gradient != 0:
                    # Negate weight gradient (if negative) and divide by AH gradient
                    # Units: (g / (s * m^2)) / (g / m^4) = m^2 / s
                    diff_factor = (-weight_gradient_per_sec) / ah_gradient
                    print(f"--- Final Calculation ---")
                    print(f"Diff Factor:      {diff_factor:.10f} m²/s")
                    print("-" * 40)
            else:
                print(f"AH Warning: Data ends before 30-min plateau reached.")
        else:
            print("No significant AH spike found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Specify folder path and diameter in mm here
    path_to_folder = r"C:\Users\taq58\Desktop\bsac\1cm_3-26_norm_plot\12-8-8_norm"
    process_experiment_data(path_to_folder, diameter_mm=10)