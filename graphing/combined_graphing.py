import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

def process_experiment_folders(base_path):
    # Get all subfolders in the base path
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    
    for folder in folders:
        folder_path = os.path.join(base_path, folder)
        print(f"Processing folder: {folder}")
        
        try:
            # 1. Locate files
            xlsx_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
            csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
            
            if not xlsx_files or not csv_files:
                print(f" Skipping {folder}: Missing .xlsx or .csv file.")
                continue
            
            weight_file = xlsx_files[0]
            humidity_file = csv_files[0]

            # 2. Load and Process Weight Data (Excel)
            df_w = pd.read_excel(weight_file, header=None)
            df_w[0] = pd.to_datetime(df_w[0], format='%b-%d-%Y %I:%M %p')
            df_w['offset'] = df_w.groupby(0).cumcount() * 10
            w_start = df_w[0].iloc[0]
            df_w['minutes'] = ((df_w[0] - w_start).dt.total_seconds() + df_w['offset']) / 60.0

            # 3. Load and Process Humidity Data (CSV)
            df_h = pd.read_csv(humidity_file, header=None, usecols=[0, 8])
            df_h[0] = pd.to_numeric(df_h[0], errors='coerce')
            df_h[8] = pd.to_numeric(df_h[8], errors='coerce')
            df_h = df_h.dropna(subset=[0, 8]).reset_index(drop=True)
            
            # --- AVERAGING LOGIC ---
            # Group by every 10 rows (10 points = 5 seconds) and take the mean
            df_h_avg = df_h.groupby(df_h.index // 10).mean()
            
            # Recalculate elapsed minutes for the averaged points
            h_start = df_h[0].iloc[0]
            # We use the averaged Unix time for the X-axis to keep it accurate
            df_h_avg['minutes'] = (df_h_avg[0] - h_start) / 60.0

            # 4. Create Combined Plot
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), sharex=True)
            
            # Top Plot: Weight (Original Resolution)
            ax1.plot(df_w['minutes'], df_w.iloc[:, 1], color='black', linewidth=0.3, antialiased=True)
            ax1.set_title(f'Experiment: {folder}\nWeight Change (10s intervals)', fontsize=14)
            ax1.set_ylabel('Weight (g)')
            
            # Bottom Plot: Humidity (Averaged/Smoothed)
            # Using a slightly thicker line (0.8) now that it's less noisy
            ax2.plot(df_h_avg['minutes'], df_h_avg[8], color='black', linewidth=0.8, antialiased=True)
            ax2.set_title('Absolute Humidity Change (5s Averaged)', fontsize=14)
            ax2.set_ylabel('Humidity (g/m³)')
            ax2.set_xlabel('Time (min)')

            # 5. Styling and Scaling
            for ax in [ax1, ax2]:
                ax.set_xlim(0, 60) 
                for spine in ax.spines.values():
                    spine.set_color('black')
                ax.tick_params(colors='black')
                ax.grid(True, which='both', linestyle='--', linewidth=0.2, color='gray')

            # 6. Save result
            output_path = os.path.join(base_path, f"{folder}.png")
            plt.tight_layout()
            plt.savefig(output_path, dpi=600)
            plt.close()
            
            print(f" Successfully saved: {output_path}")

        except Exception as e:
            print(f" Error in {folder}: {e}")

if __name__ == "__main__":
    # Ensure this script is run from the directory containing your experiment folders
    process_experiment_folders(r"C:\Users\taq58\Desktop\bsac\Previous data")