import pandas as pd
import matplotlib.pyplot as plt

def plot_all_points(file_path, output_name="detailed_weight_plot.png"):
    try:
        # 1. Load data
        # header=None assumes column 0 is Time and column 1 is Weight
        df = pd.read_excel(file_path, header=None)

        # 2. Parse Timestamps
        # This handles the "Feb-27-2026 09:09 am" format
        df[0] = pd.to_datetime(df[0], format='%b-%d-%Y %I:%M %p')

        # 3. Handle Duplicate Timestamps
        # Since you have 6 points per minute, we add a tiny 'fudge factor' 
        # (10 seconds per point) so they don't all stack on the exact same pixel.
        df['second_offset'] = df.groupby(0).cumcount() * 10 
        
        # 4. Calculate Exact Elapsed Minutes
        start_time = df[0].iloc[0]
        # Total minutes = (seconds from start + our 10s offsets) / 60
        df['elapsed_minutes'] = ((df[0] - start_time).dt.total_seconds() + df['second_offset']) / 60.0

        # 5. Create the Plot
        plt.figure(figsize=(15, 7)) # Wider figure to see high-density data
        
        # Plotting EVERY point with a very thin black line
        # linewidth=0.3 is ultra-thin to prevent a "blob" look
        plt.plot(df['elapsed_minutes'], df.iloc[:, 1], 
                 color='black', 
                 linewidth=0.3, 
                 antialiased=True)

        # 6. Aesthetics
        plt.title('High-Resolution Weight Change', color='black', fontsize=14)
        plt.xlabel('Time (min)', color='black')
        plt.ylabel('Weight (g)', color='black')
        
        # Clean black axes
        ax = plt.gca()
        for spine in ax.spines.values():
            spine.set_color('black')
        plt.tick_params(colors='black')

        # Auto-scaling logic (Matplotlib default)
        plt.autoscale(enable=True, axis='both', tight=True)
        
        # 7. Save to Image
        plt.tight_layout()
        plt.savefig(output_name, dpi=600) # 600 DPI for extreme detail
        plt.close()
        
        print(f"Done! All {len(df)} points plotted and saved to {output_name}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Ensure your file name matches here
    plot_all_points("Bottom8-4-8Top.xlsx")