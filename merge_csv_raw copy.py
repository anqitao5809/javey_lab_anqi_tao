import pandas as pd
import numpy as np
import os

def merge_sensors_with_physics(file1, file2, output_name="new_3-27_8-8-8_csv.csv"):
    try:
        # 1. Load data - columns: 0 (Unix), 2 (Temp), 3 (RH)
        cols = [0, 2, 3]
        df1 = pd.read_csv(file1, usecols=cols, skiprows=1, header=None)
        df2 = pd.read_csv(file2, usecols=cols, skiprows=1, header=None)

        # 2. Truncate Unix time to whole seconds
        df1[0] = df1[0].astype(float).apply(int)
        df2[0] = df2[0].astype(float).apply(int)

        # 3. Handle duplicates within the same second
        df1 = df1.groupby(0).mean().reset_index()
        df2 = df2.groupby(0).mean().reset_index()

        # 4. Inner Merge to align timelines
        merged = pd.merge(df1, df2, on=0, how='inner', suffixes=('_1', '_2'))

        # 5. Physics-based Absolute Humidity Calculation (g/m^3)
        def calculate_ah(temp, rh):
            # Magnus-Tetens formula for Saturation Vapor Pressure (Pa)
            # Standard AH formula: (RH/100 * Es) / (Rv * T_kelvin) * 1000
            es = 611.2 * np.exp((17.67 * temp) / (273.15 + temp))
            rv = rh/100
            tk = 216.74/(273.15 + temp) # Conversion to Kelvin for the denominator
            ah = es * rv * tk
            return ah

        merged['ah1'] = calculate_ah(merged['2_1'], merged['3_1'])
        merged['ah2'] = calculate_ah(merged['2_2'], merged['3_2'])

        # 6. Calculate Difference
        merged['ah_diff'] = merged['ah1'] - merged['ah2']

        # 7. Calculate Elapsed Seconds
        start_unix = merged[0].iloc[0]
        merged['elapsed_sec'] = merged[0] - start_unix

        # 8. Organize Columns
        # Order: Unix, Elapsed Sec, T1, RH1, AH1, T2, RH2, AH2, AH_Diff
        final_df = merged[[0, 'elapsed_sec', '2_1', '3_1', 'ah1', '2_2', '3_2', 'ah2', 'ah_diff']].copy()
        final_df.columns = [
            'unix_timestamp', 'elapsed_time_sec', 
            'temp1', 'rh1', 'ah1', 
            'temp2', 'rh2', 'ah2', 'ah_difference'
        ]

        # 9. Apply Rounding (Two decimal places for all except Unix and Elapsed)
        cols_to_round = final_df.columns[2:]
        final_df[cols_to_round] = final_df[cols_to_round].round(2)

        # 10. Save
        final_df.to_csv(output_name, index=False)
        
        print("-" * 45)
        print(f"Merge Complete.")
        print(f"Overlap Duration: {len(final_df)} seconds")
        print(f"Initial Unix:     {start_unix}")
        print(f"Saved Result to:  {output_name}")
        print("-" * 45)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    file_a = "2026-03-27-09-41-38-N-0X-CH-UNIX BotSen_D10mmTop888Bot.csv"
    file_b = "2026-03-27-09-42-06-N-1X-CH-UNIX TopSen_D10mmTop888Bot.csv"
    merge_sensors_with_physics(file_a, file_b)