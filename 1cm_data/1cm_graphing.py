import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import numpy as np

def process_and_export_graph(folder_path, min_weight_threshold=0, start_offset_min=0):
    try:
        # 1. Locate files
        xlsx_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
        csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
        
        if not xlsx_files or not csv_files:
            print(f"Error: Missing files in {folder_path}")
            return
        
        # 2. Process Humidity (CSV)
        df_h = pd.read_csv(csv_files[0], header=None, usecols=[0, 8])
        df_h[0] = pd.to_numeric(df_h[0], errors='coerce')
        df_h[8] = pd.to_numeric(df_h[8], errors='coerce')
        df_h = df_h.dropna().sort_values(0).reset_index(drop=True)
        df_h.columns = ['unix_time', 'humidity']
        df_h['unix_time'] = df_h['unix_time'].astype('int64')

        # 3. Process Weight (XLSX)
        df_w = pd.read_excel(xlsx_files[0], header=None)
        df_w['dt_naive'] = pd.to_datetime(df_w[0], format='%b-%d-%Y %I:%M %p')
        df_w['ts_fixed'] = df_w['dt_naive'].dt.tz_localize('US/Pacific')
        
        # Convert to Unix and APPLY +1 HOUR DST CORRECTION
        df_w['unix_time'] = (df_w['ts_fixed'].astype('int64') // 10**9) + 3600
        
        # Distribute samples (5s increments)
        df_w['unix_time'] += (df_w.groupby(0).cumcount() * 5)
        df_w['unix_time'] = df_w['unix_time'].astype('int64')

        # 4. TRIM TO MATCHING WINDOW
        start_time = max(df_h['unix_time'].min(), df_w['unix_time'].min())
        end_time = min(df_h['unix_time'].max(), df_w['unix_time'].max())
        
        # Apply the start offset (skipping initial minutes)
        start_time += int(start_offset_min * 60)

        if start_time >= end_time:
            print("Error: Offset or trimming resulted in no data overlap.")
            return

        df_h_trim = df_h[(df_h['unix_time'] >= start_time) & (df_h['unix_time'] <= end_time)]
        df_w_trim = df_w[(df_w['unix_time'] >= start_time) & (df_w['unix_time'] <= end_time)]

        # 5. ALIGNMENT
        df_aligned = pd.merge_asof(
            df_w_trim.sort_values('unix_time'),
            df_h_trim.sort_values('unix_time'),
            on='unix_time',
            direction='nearest',
            tolerance=10
        ).dropna(subset=['humidity'])

        df_aligned['elapsed_min'] = (df_aligned['unix_time'] - start_time) / 60.0
        
        # Rename weight column for clarity (Assumes Column Index 1 is weight)
        weight_col = df_aligned.columns[1]

        # 6. PLOTTING
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
        style = {'color': 'black', 'linewidth': 0.7}
        
        # --- WEIGHT PLOT: FILTERING LOW WEIGHTS ---
        # We create a mask where weight is ABOVE the threshold
        # This will result in gaps in the line where the weight "surged" low
        df_high_weight = df_aligned[df_aligned[weight_col] >= min_weight_threshold]
        
        ax1.plot(df_high_weight['elapsed_min'], df_high_weight[weight_col], **style)
        ax1.set_ylabel('Weight (g)', fontsize=10)
        ax1.set_title(f'Filtered Data: {os.path.basename(folder_path)}\nThreshold: >{min_weight_threshold}g, Start Offset: {start_offset_min}m', fontsize=11)
        
        # --- HUMIDITY PLOT: SHOWING FULL TIMELINE ---
        # Humidity is plotted for all aligned points, even if weight was filtered on top
        ax2.plot(df_aligned['elapsed_min'], df_aligned['humidity'], **style)
        ax2.set_ylabel('Abs Humidity (g/m³)', fontsize=10)
        ax2.set_xlabel('Elapsed Minutes (from adjusted start)', fontsize=10)
        
        for ax in [ax1, ax2]:
            ax.grid(True, linestyle=':', alpha=0.3, color='black')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        plt.tight_layout()

        # 7. EXPORT PNG
        output_filename = os.path.join(folder_path, f"filtered_plot_{min_weight_threshold}g.png")
        plt.savefig(output_filename, dpi=300)
        print(f"Success! Plot saved to: {output_filename}")
        
        plt.show()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    target_folder = r"C:\Users\taq58\Desktop\bsac\1cm_3-27_norm_plot\8-12-8_norm"
    
    # ADJUST THESE TWO VALUES:
    # min_weight_threshold: Only plot points where weight is >= this value (e.g., 450)
    # start_offset_min: Skip the first X minutes of the experiment
    process_and_export_graph(target_folder, min_weight_threshold=100, start_offset_min=2)