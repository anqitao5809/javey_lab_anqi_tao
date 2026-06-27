import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_pre_surge_baseline(file_path, output_name="baseline_detected.png"):
    try:
        # 1. Load and Clean Data
        df = pd.read_csv(file_path, header=None, usecols=[0, 8])
        df[0] = pd.to_numeric(df[0], errors='coerce')
        df[8] = pd.to_numeric(df[8], errors='coerce')
        df = df.dropna().reset_index(drop=True)

        # Calculate elapsed minutes
        start_unix = df[0].iloc[0]
        df['minutes'] = (df[0] - start_unix) / 60.0
        
        # 5 mins * 60 secs * 2 points/sec = 600 points
        window_size = 600
        
        if len(df) < window_size:
            print("Error: File too short.")
            return

        # 2. Identify the Surge point to define the search limit
        # We find where the value first crosses 20% of the max height 
        # to ensure we aren't picking the baseline inside the surge.
        surge_threshold = df[8].max() * 0.20
        surge_start_idx = (df[8] > surge_threshold).idxmax()

        # 3. Search for the baseline ONLY before the surge
        pre_surge_df = df.iloc[:surge_start_idx].copy()

        if len(pre_surge_df) < window_size:
            # Fallback: if the surge happens too early, just use the first available window
            best_end_idx = window_size
        else:
            # Rolling standard deviation to find the "flattest" 5 minutes
            # In the baseline, we care more about STABILITY (low std) than the mean.
            rolling_std = pre_surge_df[8].rolling(window=window_size).std()
            best_end_idx = rolling_std.idxmin()

        best_start_idx = best_end_idx - (window_size - 1)
        
        b_start = df['minutes'].iloc[best_start_idx]
        b_end = df['minutes'].iloc[best_end_idx]
        avg_val = df[8].iloc[best_start_idx:best_end_idx].mean()
        std_val = df[8].iloc[best_start_idx:best_end_idx].std()

        # 4. Plotting
        plt.figure(figsize=(15, 7))
        plt.plot(df['minutes'], df[8], color='black', linewidth=0.4, alpha=0.7, label='Raw Diff')
        
        # Vertical lines for the pre-surge baseline in BLUE
        plt.axvline(b_start, color='blue', linestyle='-', linewidth=2, label='Baseline Start')
        plt.axvline(b_end, color='blue', linestyle='-', linewidth=2, label='Baseline End')
        plt.axvspan(b_start, b_end, color='blue', alpha=0.15)

        # Aesthetics
        plt.title(f'Pre-Surge Baseline Detection (Stable 5-min Window)\nAvg: {avg_val:.4f} | StdDev: {std_val:.4f}', fontsize=14)
        plt.xlabel('Time (min)')
        plt.ylabel('Absolute Humidity Change (g/m³)')
        plt.xlim(0, 60)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.4)
        
        plt.tight_layout()
        plt.savefig(output_name, dpi=600)
        plt.show()

        print(f"Baseline found: {b_start:.2f} to {b_end:.2f} min")
        print(f"Mean Baseline: {avg_val:.4f}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure filename is correct
    filename = "log_only_2026-02-26_12-50-46 Bottom12-8-8Top.csv"
    plot_pre_surge_baseline(filename)