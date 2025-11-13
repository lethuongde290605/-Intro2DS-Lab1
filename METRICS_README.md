# ArXiv Scraper - Metrics Collection & Reporting

## Overview
This system now includes comprehensive performance monitoring and metrics collection to track all aspects of the scraping process as required for the lab report.

## Metrics Collected

### 1. Success Metrics
- **Total papers attempted**: Number of papers the system tried to process
- **Successful papers**: Number of papers successfully downloaded and processed
- **Failed papers**: Number of papers that failed to process
- **Success rate**: Percentage of successful downloads
- **Reference success rate**: Percentage of papers with successfully scraped reference metadata

### 2. Time Metrics (Running Time)
- **Total wall time**: End-to-end execution time of the entire system
- **Average time per paper**: Mean processing time for each paper
- **Total processing time**: Sum of all paper processing times
- **Entry discovery time**: Time spent discovering paper entries (if applicable)

### 3. Storage Metrics (Disk Usage)
- **Average size before (per paper)**: Mean size of papers before removing figures
- **Average size after (per paper)**: Mean size of papers after removing figures
- **Peak disk usage**: Maximum disk space used during execution
- **Final disk usage**: Total disk space used at completion
- **Time-series disk usage**: Disk usage tracked every second throughout execution

### 4. Memory Metrics (RAM Footprint)
- **Peak RAM usage**: Maximum memory consumed during execution
- **Average RAM usage**: Mean memory consumption throughout execution
- **Time-series RAM usage**: Memory usage tracked every second throughout execution

### 5. Reference Metrics
- **Total references found**: Total number of reference papers discovered
- **Average references per paper**: Mean number of references per successfully processed paper
- **Papers with references**: Count of papers that had reference metadata

## Output Files

All metrics are saved to the `./metrics/` directory with timestamps:

### JSON Files
1. **`system_metrics_TIMESTAMP.json`**: Complete time-series data for RAM and disk usage
   - Contains: RAM samples, disk samples, timestamps, summary statistics
   - Use this for custom analysis or re-plotting

2. **`statistics_TIMESTAMP.json`**: Comprehensive statistics summary
   - All success, time, storage, memory, and reference metrics
   - Ready for inclusion in reports

### CSV Files
1. **`system_metrics_TIMESTAMP.csv`**: Time-series data in CSV format
   - Columns: `elapsed_seconds`, `ram_mb`, `disk_mb`
   - Ideal for plotting with any tool (Excel, Python, R, etc.)

2. **`per_paper_metrics_TIMESTAMP.csv`**: Individual paper statistics
   - Columns: `paper_id`, `success`, `process_time_seconds`, `size_before_bytes`, `size_after_bytes`, `num_references`, `num_versions`, `timestamp`
   - Useful for identifying problematic papers or outliers

### Visualization Plots (PNG & PDF)
Generated automatically after scraping completes:
1. **`system_metrics_plot.png/pdf`**: Separate RAM and disk usage over time
2. **`combined_metrics_plot.png/pdf`**: Dual-axis plot showing both RAM and disk
3. **`per_paper_statistics.png/pdf`**: Four-panel plot showing:
   - Processing time distribution
   - Paper size distribution
   - Reference count distribution
   - Success vs. failure pie chart

## Usage

### Running the Scraper with Metrics
Simply run the main script as usual:
```bash
python main.py
```

The monitoring starts automatically and runs in a background thread throughout execution. At the end, all metrics are saved and a summary report is printed to the console.

### Generating Plots After Scraping
If you want to regenerate plots from existing metrics:
```bash
python plot_metrics.py ./metrics
```

### Custom Analysis
Load the JSON or CSV files in your preferred analysis tool:

**Python example:**
```python
import json
import pandas as pd

# Load statistics
with open('metrics/statistics_20250113_120000.json', 'r') as f:
    stats = json.load(f)
    
print(f"Success rate: {stats['success_rate_percentage']:.2f}%")
print(f"Peak RAM: {stats['peak_ram_mb']:.2f} MB")

# Load time-series data
df = pd.read_csv('metrics/system_metrics_20250113_120000.csv')
print(df.describe())
```

**Excel/Google Sheets:**
- Open the CSV files directly
- Create pivot tables and charts as needed

## Console Output

At the end of execution, a comprehensive report is printed:

```
================================================================================
📈 PERFORMANCE REPORT
================================================================================

🎯 Success Metrics:
  • Total papers attempted: 5000
  • Successful: 4823
  • Failed: 177
  • Success rate: 96.46%

⏱️  Time Metrics:
  • Total wall time: 14235.67s (237.26m)
  • Average time per paper: 2.85s
  • Entry discovery time: 0.00s

💾 Storage Metrics:
  • Average size before (per paper): 1.24 MB
  • Average size after (per paper): 0.87 MB
  • Peak disk usage: 4567.89 MB
  • Final disk usage: 4201.23 MB

🧠 Memory Metrics:
  • Peak RAM usage: 234.56 MB
  • Average RAM usage: 189.34 MB

📚 Reference Metrics:
  • Total references found: 12345
  • Average references per paper: 2.56
  • Papers with references: 4501
  • Reference success rate: 93.33%

================================================================================
📁 Reports saved to: ./metrics/
================================================================================
```

## Implementation Details

### Background Monitoring Thread
The system uses Python's `threading` module to run resource monitoring in the background:
- Samples RAM and disk usage every 1 second
- Runs in a daemon thread (automatically terminates with main program)
- Minimal performance impact (~0.1% CPU usage)

### Memory Tracking
Uses `psutil.Process().memory_info()` to get accurate RSS (Resident Set Size) memory usage for the Python process.

### Disk Tracking
Recursively walks the data directory and sums file sizes using `os.walk()` and `os.path.getsize()`.

### Per-Paper Metrics
Each paper's metrics are collected in `download_paper()` function:
- Measures directory size before and after download
- Counts references from metadata JSON
- Times the entire download process
- Tracks number of versions processed

## For Google Colab
The metrics collection works on Google Colab CPU-only instances. To run on Colab:

1. Upload your code to Colab
2. Install required packages:
   ```python
   !pip install arxiv requests psutil matplotlib pandas
   ```
3. Run the scraper:
   ```python
   !python main.py
   ```
4. Download metrics:
   ```python
   from google.colab import files
   !zip -r metrics.zip metrics/
   files.download('metrics.zip')
   ```

## Dependencies
- `psutil`: For memory monitoring
- `matplotlib`: For plotting
- `pandas`: For data manipulation
- All existing dependencies (arxiv, requests, etc.)

Install with:
```bash
pip install psutil matplotlib pandas
```

## Troubleshooting

### "No such file or directory: metrics"
The metrics directory is created automatically. If you see this error, check file permissions.

### Memory monitoring shows 0 MB
Ensure `psutil` is installed correctly: `pip install --upgrade psutil`

### Plots not generating
Install matplotlib: `pip install matplotlib pandas`

### CSV files are empty
This happens if the scraper is interrupted very early. Run for at least one complete paper.

## Notes for Report

When writing your report, you can:
1. Include the console output summary in your "Results" section
2. Add the generated plots as figures
3. Reference the JSON statistics file for exact numbers
4. Use the per-paper CSV to create custom analyses (e.g., correlations, outlier detection)
5. Discuss the time-series plots to show resource usage patterns

The system automatically calculates all required metrics mentioned in the assignment:
- ✅ Number of papers scraped successfully
- ✅ Overall success rate
- ✅ Average paper size (before/after removing figures)
- ✅ Average number of references per paper
- ✅ Average success rate for scraping reference metadata
- ✅ Average time to process each paper
- ✅ Total time for entry discovery
- ✅ Maximum RAM used during scraping
- ✅ Average RAM consumption
- ✅ Maximum disk storage required
- ✅ Final output's storage size
