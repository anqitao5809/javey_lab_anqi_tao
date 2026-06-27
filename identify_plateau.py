import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_priority_plateau(file_path, output_name="priority_plateau_detected_848.png"):
    try:
        # 1. Load and Clean Data
        df = pd.read_csv(file_path, header=None, usecols=[0, 8])
        df[0] = pd.to_numeric(df[0], errors='coerce')
        df[8] = pd.to_numeric(df[8], errors='coerce')
        df = df.dropna().reset_index(drop=True)

        start_unix = df[0].iloc[0]
        df['minutes'] = (df[0] - start_unix) / 60.0
        
        window_size = 1200 # 10 minutes
        
        if len(df) < window_size:
            print("Error: File too short.")
            return

        # 2. Calculate Rolling Metrics
        rolling_mean = df[8].rolling(window=window_size).mean()
        rolling_std = df[8].rolling(window=window_size).std()

        # 3. Priority Logic
        # Step A: Find the highest average value reached by any 10-min window
        max_possible_mean = rolling_mean.max()
        
        # Step B: Filter for windows that are "High Enough" 
        # (Within 5% of the absolute maximum average)
        # This forces the algorithm to stay at the top of the graph.
        high_value_threshold = max_possible_mean * 0.95
        high_value_indices = rolling_mean[rolling_mean >= high_value_threshold].index
        
        if high_value_indices.empty:
            best_end_idx = rolling_mean.idxmax()
        else:
            # Step C: Among these high-value windows, pick the one with the LEAST noise
            best_end_idx = rolling_std[high_value_indices].idxmin()

        best_start_idx = best_end_idx - (window_size - 1)
        
        p_start = df['minutes'].iloc[best_start_idx]
        p_end = df['minutes'].iloc[best_end_idx]
        avg_val = df[8].iloc[best_start_idx:best_end_idx].mean()
        std_val = df[8].iloc[best_start_idx:best_end_idx].std()

        # 4. Plotting
        plt.figure(figsize=(15, 7))
        plt.plot(df['minutes'], df[8], color='black', linewidth=0.4, alpha=0.7, label='Raw Diff')
        
        # Highlight plateau
        plt.axvline(p_start, color='red', linestyle='-', linewidth=2, label='Plateau Start')
        plt.axvline(p_end, color='red', linestyle='-', linewidth=2, label='Plateau End')
        plt.axvspan(p_start, p_end, color='red', alpha=0.15)

        plt.title(f'Priority Plateau (Top 5% Avg + Min Noise)\nAvg: {avg_val:.4f} | StdDev: {std_val:.4f}', fontsize=14)
        plt.xlabel('Time (min)')
        plt.ylabel('Absolute Humidity Change (g/m³)')
        plt.xlim(0, 60)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_name, dpi=600)
        plt.show()

        print(f"Plateau found: {p_start:.2f} to {p_end:.2f} min")
        print(f"Average Value: {avg_val:.4f}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    filename = "log_only_2026-02-27_09-12-16 Bottom8-4-8Top.csv"
    plot_priority_plateau(filename)
