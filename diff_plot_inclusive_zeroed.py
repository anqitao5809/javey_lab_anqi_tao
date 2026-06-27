import pandas as pd
import matplotlib.pyplot as plt

def plot_csv_diff(file_path, output_name="3-26_12-8-8_norm.png"):
    try:
        # 1. Load and Clean Data
        df = pd.read_csv(file_path, header=None, usecols=[0, 8])
        df[0] = pd.to_numeric(df[0], errors='coerce')
        df[8] = pd.to_numeric(df[8], errors='coerce')
        df = df.dropna(subset=[0, 8]).reset_index(drop=True)

        # 2. Handle Sub-second Precision & Elapsed Time
        # Assuming 2 points per second (120 points per minute)
        df['sub_second_offset'] = df.groupby(0).cumcount() * 0.5
        start_time_unix = df[0].iloc[0]
        df['elapsed_minutes'] = ((df[0] - start_time_unix) + df['sub_second_offset']) / 60.0

        # 3. Sliding Window Detection (10-minute window / 1.5 Spike)
        # 10 minutes at 2 samples/sec = 1200 rows
        window_size_rows = 300
        
        # Calculate the difference between current point and the point 10 mins ago
        df['window_diff'] = df[8].diff(periods=window_size_rows)
        
        # Find the first index where the 10-minute increase exceeds 1.5
        trigger_indices = df.index[df['window_diff'] > 1.5].tolist()

        if trigger_indices:
            trigger_idx = trigger_indices[0]
            # Baseline is the point at the START of that 10-minute window
            baseline_idx = max(0, trigger_idx - window_size_rows)
            baseline_value = df.loc[baseline_idx, 8]
            spike_start_time = df.loc[baseline_idx, 'elapsed_minutes']
        else:
            # Fallback if no 1.5 spike is found
            baseline_value = df[8].iloc[0]
            spike_start_time = 0
            print("No 1.5 increase found within any 10-minute window.")

        # 4. Normalize the entire dataset
        df['normalized_ah'] = df[8] - baseline_value

        # 5. Create the High-Resolution Plot
        plt.figure(figsize=(16, 8))
        
        plt.plot(df['elapsed_minutes'], df['normalized_ah'], 
                 color='black', 
                 linewidth=0.3, 
                 antialiased=True)

        # 6. Aesthetics & Full Duration Scaling
        plt.title('Normalized AH Change (10min Window / 1.5g/m³ Spike)', fontsize=14)
        plt.xlabel('Time (min)', fontsize=12)
        plt.ylabel('Δ Absolute Humidity (g/m³)', fontsize=12)
        
        # Ensure the plot covers the entire CSV duration
        plt.xlim(0, df['elapsed_minutes'].max())
        
        # Reference line at 0
        plt.axhline(0, color='red', linestyle='--', linewidth=0.8, alpha=0.6)
        
        if trigger_indices:
            plt.axvline(spike_start_time, color='blue', linestyle=':', label=f'Baseline at {spike_start_time:.2f} min')
            plt.legend()

        # Clean Style
        ax = plt.gca()
        for spine in ax.spines.values():
            spine.set_color('black')
        plt.grid(True, which='both', linestyle='--', alpha=0.2)

        # 7. Save to Image
        plt.tight_layout()
        plt.savefig(output_name, dpi=600)
        plt.close()
        
        print(f"Success! Processed {len(df)} points.")
        if trigger_indices:
            print(f"Spike triggered. Baseline set at {spike_start_time:.2f} minutes.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    plot_csv_diff("new_3-26_12-8-8_csv.csv")