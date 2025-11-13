#!/usr/bin/env python3
"""
ArXiv Batch Downloader with Progress Tracking
Main entry point for the application - supports multithreading
"""
import time
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from config_manager import load_config, save_config
from arxiv_client import format_arxiv_id, get_latest_version
from downloader import download_paper
from metrics_collector import MetricsCollector, PaperMetrics
from shared import config_lock


def process_paper(arxiv_id, config, config_path, paper_metrics, settings):
    """
    Process a single paper (download + collect metrics)
    Thread-safe function to be called by thread pool
    
    Args:
        arxiv_id: ArXiv paper ID
        config: Configuration dictionary
        config_path: Path to config file
        paper_metrics: PaperMetrics collector
        settings: Download settings
        
    Returns:
        tuple: (arxiv_id, success, paper_info)
    """
    safe_id = format_arxiv_id(arxiv_id)
    
    print(f"\n{'='*80}")
    print(f"📄 Processing: {arxiv_id}")
    print(f"{'='*80}")
    
    # Time the paper processing
    paper_start_time = time.time()
    success, paper_info = download_paper(arxiv_id, config, config_path, collect_metrics=True)
    paper_end_time = time.time()
    
    # Record metrics (thread-safe)
    paper_metrics.add_paper(
        paper_id=arxiv_id,
        success=success,
        process_time=paper_end_time - paper_start_time,
        size_before=paper_info.get('size_before', 0),
        size_after=paper_info.get('size_after', 0),
        num_references=paper_info.get('num_references', 0),
        num_versions=paper_info.get('num_versions', 0),
        reference_fetch_success=paper_info.get('reference_fetch_success', False)
    )
    
    # Update config progress (thread-safe)
    with config_lock:
        if success:
            if safe_id not in config["progress"]["completed_papers"]:
                config["progress"]["completed_papers"].append(safe_id)
        else:
            if safe_id not in config["progress"]["failed_papers"]:
                config["progress"]["failed_papers"].append(safe_id)
        
        # Save progress periodically
        save_config(config, config_path)
    
    # Delay between papers
    if success:
        time.sleep(settings["delay_between_papers"])
    else:
        print(f"⚠️  Failed to process {arxiv_id}")
        time.sleep(settings["delay_between_papers"] * 2)
    
    return arxiv_id, success, paper_info


def main():
    """Main execution function for batch downloading arXiv papers with multithreading"""
    config_path = "config.json"
    
    # Load config
    config = load_config(config_path)
    progress = config["progress"]
    settings = config["download_settings"]
    max_workers = settings.get("max_workers", 5)  # Default to 5 if not set
    
    # Initialize metrics collectors
    metrics_dir = "./metrics"
    os.makedirs(metrics_dir, exist_ok=True)
    
    system_monitor = MetricsCollector(data_dir=settings['base_dir'], interval=1.0)
    paper_metrics = PaperMetrics()
    
    # Start monitoring
    system_monitor.start_monitoring()
    paper_metrics.start_timing()
    
    print("=" * 80)
    print("🚀 ArXiv Batch Downloader with Progress Tracking (Multithreaded)")
    print("=" * 80)
    print(f"📁 Output directory: {settings['base_dir']}")
    print(f"📊 Range: {progress['prefix']}.{progress['start']:05d} to {progress['prefix']}.{progress['end']:05d}")
    print(f"📈 Current progress: {progress['current']}")
    print(f"✅ Completed: {len(progress['completed_papers'])} papers")
    print(f"❌ Failed: {len(progress['failed_papers'])} papers")
    print(f"🧵 Max workers: {max_workers}")
    print("=" * 80)
    
    # Resume from last position
    start_from = progress["current"]
    
    # Build list of papers to process
    papers_to_process = []
    for i in range(start_from, progress["end"] + 1):
        arxiv_id = f"{progress['prefix']}.{i:05d}"
        safe_id = format_arxiv_id(arxiv_id)
        
        # Skip if already completed
        if safe_id in progress["completed_papers"]:
            print(f"⏭️  Skipping {arxiv_id} (already completed)")
            continue
        
        papers_to_process.append((i, arxiv_id))
    
    print(f"\n📋 Total papers to process: {len(papers_to_process)}")
    print("=" * 80)
    
    try:
        # Process papers using thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_paper = {
                executor.submit(process_paper, arxiv_id, config, config_path, paper_metrics, settings): (idx, arxiv_id)
                for idx, arxiv_id in papers_to_process
            }
            
            # Process completed tasks
            completed = 0
            for future in as_completed(future_to_paper):
                idx, arxiv_id = future_to_paper[future]
                completed += 1
                
                try:
                    result_id, success, paper_info = future.result()
                    
                    # Update current position
                    with config_lock:
                        progress["current"] = max(progress["current"], idx)
                    
                    status = "✅" if success else "❌"
                    print(f"\n{status} [{completed}/{len(papers_to_process)}] Completed: {result_id}")
                    
                except Exception as e:
                    print(f"\n❌ Exception processing {arxiv_id}: {e}")
                    with config_lock:
                        safe_id = format_arxiv_id(arxiv_id)
                        if safe_id not in config["progress"]["failed_papers"]:
                            config["progress"]["failed_papers"].append(safe_id)
        
        print("\n" + "=" * 80)
        print("🎉 Download completed!")
        print(f"✅ Successfully downloaded: {len(progress['completed_papers'])} papers")
        print(f"❌ Failed: {len(progress['failed_papers'])} papers")
        if progress['failed_papers']:
            print(f"⚠️  Failed papers: {', '.join(progress['failed_papers'][:10])}...")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Download interrupted by user")
        print("💾 Progress saved. You can resume by running this script again.")
        save_config(config, config_path)
        
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("💾 Saving progress...")
        save_config(config, config_path)
        raise
    
    finally:
        # Stop monitoring and save metrics
        print("\n" + "=" * 80)
        print("📊 Saving metrics and generating reports...")
        print("=" * 80)
        
        system_monitor.stop_monitoring()
        
        # Generate timestamp for reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save system metrics
        system_monitor.save_time_series(f"{metrics_dir}/system_metrics_{timestamp}.json")
        system_monitor.save_csv_for_plotting(f"{metrics_dir}/system_metrics_{timestamp}.csv")
        
        # Save paper metrics
        paper_metrics.save_per_paper_csv(f"{metrics_dir}/per_paper_metrics_{timestamp}.csv")
        paper_metrics.save_statistics_json(f"{metrics_dir}/statistics_{timestamp}.json")
        
        # Print summary statistics
        stats = paper_metrics.get_statistics()
        sys_stats = system_monitor.get_summary_stats()
        
        print("\n" + "=" * 80)
        print("📈 PERFORMANCE REPORT")
        print("=" * 80)
        print(f"\n🎯 Success Metrics:")
        print(f"  • Total papers attempted: {stats['total_papers_attempted']}")
        print(f"  • Successful: {stats['successful_papers']}")
        print(f"  • Failed: {stats['failed_papers']}")
        print(f"  • Success rate: {stats['success_rate_percentage']:.2f}%")
        
        print(f"\n⏱️  Time Metrics:")
        print(f"  • Total wall time: {stats['total_wall_time_seconds']:.2f}s ({stats['total_wall_time_seconds']/60:.2f}m)")
        print(f"  • Average time per paper: {stats['average_time_per_paper_seconds']:.2f}s")
        print(f"  • Entry discovery time: {stats['entry_discovery_time_seconds']:.2f}s")
        
        print(f"\n💾 Storage Metrics:")
        print(f"  • Average size before (per paper): {stats['average_size_before_mb']:.2f} MB")
        print(f"  • Average size after (per paper): {stats['average_size_after_mb']:.2f} MB")
        print(f"  • Peak disk usage: {sys_stats['peak_disk_mb']:.2f} MB")
        print(f"  • Final disk usage: {sys_stats['final_disk_mb']:.2f} MB")
        
        print(f"\n🧠 Memory Metrics:")
        print(f"  • Peak RAM usage: {sys_stats['peak_ram_mb']:.2f} MB")
        print(f"  • Average RAM usage: {sys_stats['average_ram_mb']:.2f} MB")
        
        print(f"\n📚 Reference Metrics:")
        print(f"  • Total references found: {stats['total_references_found']}")
        print(f"  • Average references per paper: {stats['average_references_per_paper']:.2f}")
        print(f"  • Papers with references: {stats['papers_with_references']}")
        print(f"  • Reference success rate: {stats['reference_success_rate']*100:.2f}%")
        
        print("\n" + "=" * 80)
        print(f"📁 Reports saved to: {metrics_dir}/")
        print("=" * 80)


if __name__ == "__main__":
    main()
