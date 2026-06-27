import pandas as pd
import matplotlib.pyplot as plt

def plot_csv_diff(file_path, output_name="high_res_diff_plot.png"):
    try:
        # 1. Load CSV data
        # usecols=[0, 8] reads only Unix Time (0) and Diff Factor (8/Column I)
        df = pd.read_csv(file_path, header=None, usecols=[0, 8])

        # 2. Convert to Numeric
        # This converts strings to numbers and turns non-numeric text into 'NaN'
        df[0] = pd.to_numeric(df[0], errors='coerce')
        df[8] = pd.to_numeric(df[8], errors='coerce')
        
        # Drop any rows that failed conversion (like headers)
        df = df.dropna(subset=[0, 8])

        # 3. Handle Sub-second Precision (2 points per second)
        # We add 0.5s to the second point of each duplicate Unix timestamp
        df['sub_second_offset'] = df.groupby(0).cumcount() * 0.5
        
        # 4. Calculate Elapsed Minutes
        start_time_unix = df[0].iloc[0]
        df['elapsed_minutes'] = ((df[0] - start_time_unix) + df['sub_second_offset']) / 60.0

        # 5. Create the High-Resolution Plot
        plt.figure(figsize=(15, 7))
        
        plt.plot(df['elapsed_minutes'], df[8], 
                 color='black', 
                 linewidth=0.3, 
                 antialiased=True)

        # 6. Aesthetics & Scaling
        plt.title('High-Resolution Diff Factor Change', color='black', fontsize=14)
        plt.xlabel('Time (min)', color='black')
        plt.ylabel('Absolute Humidity Change(g/m3)', color='black')
        
        # Hard scale from 0 to 60 minutes
        plt.xlim(0, 60)
        
        # Clean black axes style
        ax = plt.gca()
        for spine in ax.spines.values():
            spine.set_color('black')
        plt.tick_params(colors='black')

        # 7. Save to Image with 600 DPI
        plt.tight_layout()
        plt.savefig(output_name, dpi=600)
        plt.close()
        
        print(f"Done! Successfully plotted {len(df)} points to {output_name}")

    except Exception as e:
        print(f"Error processing file: {e}")


if __name__ == "__main__":
    # Replace 'your_data.csv' with your actual filename
    plot_csv_diff("new_data_csv.csv")