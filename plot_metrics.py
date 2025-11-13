"""
Plot Metrics Module
Generate visualizations from collected metrics data
"""
import json
import matplotlib.pyplot as plt
import pandas as pd
import os


def plot_system_metrics(csv_path, output_dir="./metrics"):
    """
    Create plots for RAM and disk usage over time
    
    Args:
        csv_path: Path to CSV file with system metrics
        output_dir: Directory to save plots
    """
    # Read data
    df = pd.read_csv(csv_path)
    
    # Convert elapsed seconds to minutes for better readability
    df['elapsed_minutes'] = df['elapsed_seconds'] / 60
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot RAM usage
    ax1.plot(df['elapsed_minutes'], df['ram_mb'], 
             color='#3498db', linewidth=2, label='RAM Usage')
    ax1.fill_between(df['elapsed_minutes'], df['ram_mb'], 
                      alpha=0.3, color='#3498db')
    ax1.set_xlabel('Time (minutes)', fontsize=12)
    ax1.set_ylabel('RAM Usage (MB)', fontsize=12)
    ax1.set_title('Memory Usage Over Time', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Add peak annotation
    peak_idx = df['ram_mb'].idxmax()
    peak_time = df.loc[peak_idx, 'elapsed_minutes']
    peak_ram = df.loc[peak_idx, 'ram_mb']
    ax1.annotate(f'Peak: {peak_ram:.1f} MB', 
                 xy=(peak_time, peak_ram),
                 xytext=(peak_time, peak_ram * 1.1),
                 arrowprops=dict(arrowstyle='->', color='red'),
                 fontsize=10, color='red')
    
    # Plot Disk usage
    ax2.plot(df['elapsed_minutes'], df['disk_mb'], 
             color='#2ecc71', linewidth=2, label='Disk Usage')
    ax2.fill_between(df['elapsed_minutes'], df['disk_mb'], 
                      alpha=0.3, color='#2ecc71')
    ax2.set_xlabel('Time (minutes)', fontsize=12)
    ax2.set_ylabel('Disk Usage (MB)', fontsize=12)
    ax2.set_title('Storage Usage Over Time', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # Add final size annotation
    final_disk = df['disk_mb'].iloc[-1]
    final_time = df['elapsed_minutes'].iloc[-1]
    ax2.annotate(f'Final: {final_disk:.1f} MB', 
                 xy=(final_time, final_disk),
                 xytext=(final_time * 0.7, final_disk * 1.1),
                 arrowprops=dict(arrowstyle='->', color='darkgreen'),
                 fontsize=10, color='darkgreen')
    
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'system_metrics_plot.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved plot to {output_path}")
    
    # Also save as PDF
    output_path_pdf = os.path.join(output_dir, 'system_metrics_plot.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    print(f"✅ Saved plot to {output_path_pdf}")
    
    plt.close()


def plot_combined_metrics(csv_path, output_dir="./metrics"):
    """
    Create a combined plot showing both RAM and disk on the same chart
    
    Args:
        csv_path: Path to CSV file with system metrics
        output_dir: Directory to save plots
    """
    # Read data
    df = pd.read_csv(csv_path)
    df['elapsed_minutes'] = df['elapsed_seconds'] / 60
    
    # Create figure with dual y-axis
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Plot RAM on left axis
    color1 = '#3498db'
    ax1.set_xlabel('Time (minutes)', fontsize=12)
    ax1.set_ylabel('RAM Usage (MB)', fontsize=12, color=color1)
    line1 = ax1.plot(df['elapsed_minutes'], df['ram_mb'], 
                     color=color1, linewidth=2, label='RAM Usage')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.fill_between(df['elapsed_minutes'], df['ram_mb'], 
                      alpha=0.2, color=color1)
    ax1.grid(True, alpha=0.3)
    
    # Create second y-axis for disk
    ax2 = ax1.twinx()
    color2 = '#2ecc71'
    ax2.set_ylabel('Disk Usage (MB)', fontsize=12, color=color2)
    line2 = ax2.plot(df['elapsed_minutes'], df['disk_mb'], 
                     color=color2, linewidth=2, label='Disk Usage')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.fill_between(df['elapsed_minutes'], df['disk_mb'], 
                      alpha=0.2, color=color2)
    
    # Title
    plt.title('Resource Usage Over Time (RAM & Disk)', 
              fontsize=14, fontweight='bold', pad=20)
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'combined_metrics_plot.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved combined plot to {output_path}")
    
    output_path_pdf = os.path.join(output_dir, 'combined_metrics_plot.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    print(f"✅ Saved combined plot to {output_path_pdf}")
    
    plt.close()


def plot_per_paper_statistics(csv_path, output_dir="./metrics"):
    """
    Create visualizations for per-paper statistics
    
    Args:
        csv_path: Path to CSV file with per-paper metrics
        output_dir: Directory to save plots
    """
    # Read data
    df = pd.read_csv(csv_path)
    
    # Filter successful papers
    df_success = df[df['success'] == True]
    
    if len(df_success) == 0:
        print("⚠️  No successful papers to plot")
        return
    
    # Create figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Processing time distribution
    ax1 = axes[0, 0]
    ax1.hist(df['process_time_seconds'], bins=30, 
             color='#3498db', alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Processing Time (seconds)', fontsize=11)
    ax1.set_ylabel('Number of Papers', fontsize=11)
    ax1.set_title('Distribution of Processing Times', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Paper sizes
    ax2 = axes[0, 1]
    sizes_mb = df_success['size_after_bytes'] / 1024 / 1024
    ax2.hist(sizes_mb, bins=30, 
             color='#2ecc71', alpha=0.7, edgecolor='black')
    ax2.set_xlabel('Paper Size (MB)', fontsize=11)
    ax2.set_ylabel('Number of Papers', fontsize=11)
    ax2.set_title('Distribution of Paper Sizes', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Number of references
    ax3 = axes[1, 0]
    ax3.hist(df_success['num_references'], bins=30, 
             color='#e74c3c', alpha=0.7, edgecolor='black')
    ax3.set_xlabel('Number of References', fontsize=11)
    ax3.set_ylabel('Number of Papers', fontsize=11)
    ax3.set_title('Distribution of Reference Counts', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Success vs Failed
    ax4 = axes[1, 1]
    success_counts = df['success'].value_counts()
    colors = ['#2ecc71', '#e74c3c']
    ax4.pie(success_counts, labels=['Success', 'Failed'], 
            autopct='%1.1f%%', colors=colors, startangle=90)
    ax4.set_title('Success Rate', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'per_paper_statistics.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved per-paper statistics to {output_path}")
    
    output_path_pdf = os.path.join(output_dir, 'per_paper_statistics.pdf')
    plt.savefig(output_path_pdf, bbox_inches='tight')
    print(f"✅ Saved per-paper statistics to {output_path_pdf}")
    
    plt.close()


def generate_all_plots(metrics_dir="./metrics"):
    """
    Generate all visualization plots from metrics directory
    
    Args:
        metrics_dir: Directory containing metrics files
    """
    print("\n" + "=" * 80)
    print("📊 Generating visualization plots...")
    print("=" * 80)
    
    # Find the most recent metrics files
    import glob
    
    # System metrics
    system_csv_files = glob.glob(f"{metrics_dir}/system_metrics_*.csv")
    if system_csv_files:
        latest_system_csv = max(system_csv_files, key=os.path.getctime)
        print(f"\n📈 Plotting system metrics from: {latest_system_csv}")
        plot_system_metrics(latest_system_csv, metrics_dir)
        plot_combined_metrics(latest_system_csv, metrics_dir)
    else:
        print("⚠️  No system metrics CSV files found")
    
    # Per-paper metrics
    paper_csv_files = glob.glob(f"{metrics_dir}/per_paper_metrics_*.csv")
    if paper_csv_files:
        latest_paper_csv = max(paper_csv_files, key=os.path.getctime)
        print(f"\n📊 Plotting per-paper statistics from: {latest_paper_csv}")
        plot_per_paper_statistics(latest_paper_csv, metrics_dir)
    else:
        print("⚠️  No per-paper metrics CSV files found")
    
    print("\n" + "=" * 80)
    print("✅ All plots generated successfully!")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    
    metrics_dir = sys.argv[1] if len(sys.argv) > 1 else "./metrics"
    generate_all_plots(metrics_dir)
