#!/usr/bin/env python3
"""
Test script for metrics collection system
"""
import time
import os
from metrics_collector import MetricsCollector, PaperMetrics

def test_metrics_system():
    """Test the metrics collection system"""
    print("=" * 80)
    print("🧪 Testing Metrics Collection System")
    print("=" * 80)
    
    # Create test directory
    test_dir = "./test_data"
    os.makedirs(test_dir, exist_ok=True)
    
    # Initialize collectors
    print("\n1. Initializing collectors...")
    system_monitor = MetricsCollector(data_dir=test_dir, interval=0.5)
    paper_metrics = PaperMetrics()
    
    # Start monitoring
    print("2. Starting system monitoring...")
    system_monitor.start_monitoring()
    paper_metrics.start_timing()
    
    # Simulate some work
    print("3. Simulating paper processing...")
    for i in range(5):
        print(f"   Processing paper {i+1}/5...")
        
        # Simulate work
        time.sleep(1)
        
        # Create some test files
        test_file = os.path.join(test_dir, f"test_paper_{i}.txt")
        with open(test_file, 'w') as f:
            f.write("Test content " * 1000)
        
        # Record metrics
        paper_metrics.add_paper(
            paper_id=f"test-{i:05d}",
            success=True,
            process_time=1.0 + i * 0.1,
            size_before=0,
            size_after=os.path.getsize(test_file),
            num_references=10 + i,
            num_versions=1
        )
    
    print("4. Stopping monitoring...")
    system_monitor.stop_monitoring()
    
    # Get statistics
    print("\n5. Collecting statistics...")
    stats = paper_metrics.get_statistics()
    sys_stats = system_monitor.get_summary_stats()
    
    # Print results
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS")
    print("=" * 80)
    
    print(f"\n✅ Success Metrics:")
    print(f"   • Total papers: {stats['total_papers_attempted']}")
    print(f"   • Success rate: {stats['success_rate_percentage']:.2f}%")
    
    print(f"\n⏱️  Time Metrics:")
    print(f"   • Total time: {stats['total_wall_time_seconds']:.2f}s")
    print(f"   • Avg per paper: {stats['average_time_per_paper_seconds']:.2f}s")
    
    print(f"\n🧠 Memory Metrics:")
    print(f"   • Peak RAM: {sys_stats['peak_ram_mb']:.2f} MB")
    print(f"   • Avg RAM: {sys_stats['average_ram_mb']:.2f} MB")
    print(f"   • Samples collected: {sys_stats['sample_count']}")
    
    print(f"\n💾 Disk Metrics:")
    print(f"   • Final size: {sys_stats['final_disk_mb']:.2f} MB")
    print(f"   • Peak size: {sys_stats['peak_disk_mb']:.2f} MB")
    
    # Save test metrics
    print("\n6. Saving test reports...")
    metrics_dir = "./test_metrics"
    os.makedirs(metrics_dir, exist_ok=True)
    
    system_monitor.save_time_series(f"{metrics_dir}/system_test.json")
    system_monitor.save_csv_for_plotting(f"{metrics_dir}/system_test.csv")
    paper_metrics.save_per_paper_csv(f"{metrics_dir}/per_paper_test.csv")
    paper_metrics.save_statistics_json(f"{metrics_dir}/statistics_test.json")
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")
    print("=" * 80)
    
    # Cleanup
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    return True

if __name__ == "__main__":
    try:
        test_metrics_system()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
