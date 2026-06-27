import pandas as pd
import numpy as np
import os
import glob

def merge_sensors_from_folder(folder_path, output_name="new_3-27_8-8-8_csv.csv"):
    try:
        # 1. Identify files starting with '2026' in the provided folder
        search_pattern = os.path.join(folder_path, "2026*.csv")
        files = glob.glob(search_pattern)
        
        # Exclude the output file from the search if it already exists to avoid self-merging
        files = [f for f in files if os.path.basename(f) != output_name]
        
        if len(files) < 2:
            print(f"Error: Found only {len(files)} source files starting with '2026' in {folder_path}. Need at least 2.")
            return
        
        # Sort files to ensure consistent ordering (Sensor 1 vs Sensor 2)
        files.sort()
        file1 = files[0]
        file2 = files[1]
        
        print(f"Processing:\n- {os.path.basename(file1)}\n- {os.path.basename(file2)}")

        # 2. Load data - columns: 0 (Unix), 2 (Temp), 3 (RH)
        cols = [0, 2, 3]
        df1 = pd.read_csv(file1, usecols=cols, skiprows=1, header=None)
        df2 = pd.read_csv(file2, usecols=cols, skiprows=1, header=None)

        # 3. Truncate Unix time to whole seconds
        df1[0] = df1[0].astype(float).apply(int)
        df2[0] = df2[0].astype(float).apply(int)

        # 4. Handle duplicates within the same second
        df1 = df1.groupby(0).mean().reset_index()
        df2 = df2.groupby(0).mean().reset_index()

        # 5. Inner Merge to align timelines
        merged = pd.merge(df1, df2, on=0, how='inner', suffixes=('_1', '_2'))

        # 6. Physics-based Absolute Humidity Calculation (g/m^3)
        # Using the specific constants provided in your latest snippet
        def calculate_ah(temp, rh):
            # es: Saturation vapor pressure
            es = 6.112 * np.exp((17.67 * temp) / (273.15 + temp))
            rv = rh / 100.0
            # tk: Temperature correction factor
            tk = 216.74 / (273.15 + temp) 
            ah = es * rv * tk
            return ah

        merged['ah1'] = calculate_ah(merged['2_1'], merged['3_1'])
        merged['ah2'] = calculate_ah(merged['2_2'], merged['3_2'])

        # 7. Calculate Difference
        merged['ah_diff'] = merged['ah1'] - merged['ah2']

        # 8. Calculate Elapsed Seconds
        start_unix = merged[0].iloc[0]
        merged['elapsed_sec'] = merged[0] - start_unix

        # 9. Organize Columns
        final_df = merged[[0, 'elapsed_sec', '2_1', '3_1', 'ah1', '2_2', '3_2', 'ah2', 'ah_diff']].copy()
        final_df.columns = [
            'unix_timestamp', 'elapsed_time_sec', 
            'temp1', 'rh1', 'ah1', 
            'temp2', 'rh2', 'ah2', 'ah_difference'
        ]

        # 10. Apply Rounding
        cols_to_round = final_df.columns[2:]
        final_df[cols_to_round] = final_df[cols_to_round].round(2)

        # 11. Save in the folder provided (overwrites if file exists)
        output_path = os.path.join(folder_path, output_name)
        final_df.to_csv(output_path, index=False)
        
        print("-" * 45)
        print(f"Merge Complete.")
        print(f"Overlap Duration: {len(final_df)} seconds")
        print(f"Initial Unix:     {start_unix}")
        print(f"Saved Result to:  {output_path}")
        print("-" * 45)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # PROVIDE YOUR FOLDER PATH HERE
    path_to_folder = r"C:\Users\taq58\Desktop\bsac\1cm_3-27_norm_plot\8-12-8_norm"
    
    # Name the output file
    output_filename = "new_3-27_8-12-8_csv.csv"
    
    merge_sensors_from_folder(path_to_folder, output_filename)