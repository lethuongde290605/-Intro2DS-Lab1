"""
Metrics Collector Module
Real-time monitoring of system resources (RAM, disk usage) during scraping
Uses background thread to collect metrics at regular intervals
"""
import psutil
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional
import json


class MetricsCollector:
    """
    Collects system metrics (RAM, disk usage) in real-time using a background thread
    Includes auto-save functionality for Colab resilience
    """
    
    def __init__(self, data_dir: str, interval: float = 1.0, checkpoint_dir: str = "./metrics"):
        """
        Initialize metrics collector
        
        Args:
            data_dir: Directory to monitor for disk usage
            interval: Sampling interval in seconds
            checkpoint_dir: Directory to save checkpoints for resume capability
        """
        self.data_dir = data_dir
        self.interval = interval
        self.checkpoint_dir = checkpoint_dir
        self.process = psutil.Process(os.getpid())
        
        # Metrics storage (combined samples)
        self.samples: List[Dict] = []  # Each sample has: timestamp, elapsed_seconds, ram_mb, disk_mb
        
        # Threading
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Peak values
        self.peak_ram_mb = 0.0
        self.peak_disk_mb = 0.0
        
        # Start time
        self.start_time: Optional[float] = None
        
        # Checkpoint file paths
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.checkpoint_path = os.path.join(checkpoint_dir, "system_metrics_checkpoint.json")
        # Checkpoint file paths
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.checkpoint_path = os.path.join(checkpoint_dir, "system_metrics_checkpoint.json")
        
    def load_checkpoint(self) -> bool:
        """
        Load metrics from checkpoint file (for resume after Colab disconnect)
        
        Returns:
            bool: True if checkpoint was loaded successfully
        """
        if not os.path.exists(self.checkpoint_path):
            print("📂 No checkpoint found - starting fresh")
            return False
        
        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.samples = data.get('samples', [])
            self.peak_ram_mb = data.get('peak_ram_mb', 0.0)
            self.peak_disk_mb = data.get('peak_disk_mb', 0.0)
            self.start_time = data.get('start_time')
            
            print(f"✅ Loaded checkpoint with {len(self.samples)} samples")
            print(f"   Peak RAM: {self.peak_ram_mb:.2f} MB")
            print(f"   Peak Disk: {self.peak_disk_mb:.2f} MB")
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to load checkpoint: {e}")
            return False
    
    def save_checkpoint(self):
        """Save current metrics to checkpoint file"""
        try:
            data = {
                'samples': self.samples,
                'peak_ram_mb': self.peak_ram_mb,
                'peak_disk_mb': self.peak_disk_mb,
                'start_time': self.start_time,
                'last_saved': time.time()
            }
            
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Failed to save checkpoint: {e}")
    
    def start_monitoring(self, autosave_interval: float = 30.0):
        """
        Start background monitoring thread
        NOTE: autosave_interval is deprecated - checkpoint is saved after each sample
        
        Args:
            autosave_interval: Ignored (kept for backward compatibility)
        """
        if self.monitoring:
            return
            
        self.monitoring = True
        
        # Set start time if not resuming
        if self.start_time is None:
            self.start_time = time.time()
        
        # Start monitoring thread (saves checkpoint after each sample)
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print(f"📊 Started system monitoring (sampling & saving every {self.interval}s)")
        
    def stop_monitoring(self):
        """Stop background monitoring thread and save final checkpoint"""
        if not self.monitoring:
            return
            
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        
        # Final save
        self.save_checkpoint()
        print("📊 Stopped system monitoring (final checkpoint saved)")
        
    def _monitor_loop(self):
        """Background monitoring loop - runs in separate thread"""
        while self.monitoring:
            try:
                current_time = time.time()
                elapsed = current_time - self.start_time if self.start_time else 0
                
                # Get RAM usage
                memory_info = self.process.memory_info()
                ram_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                
                # Get disk usage of data directory
                disk_mb = self._get_directory_size(self.data_dir) / 1024 / 1024
                
                # Store combined sample
                self.samples.append({
                    'timestamp': current_time,
                    'elapsed_seconds': elapsed,
                    'ram_mb': ram_mb,
                    'disk_mb': disk_mb
                })
                
                # Update peaks
                self.peak_ram_mb = max(self.peak_ram_mb, ram_mb)
                self.peak_disk_mb = max(self.peak_disk_mb, disk_mb)
                
                # Save checkpoint immediately after collecting sample
                self.save_checkpoint()
                print(f"💾 Collected & saved metrics (sample #{len(self.samples)}: RAM={ram_mb:.2f}MB, Disk={disk_mb:.2f}MB)")
                
                time.sleep(self.interval)
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                time.sleep(self.interval)
    
    def _get_directory_size(self, path: str) -> int:
        """
        Calculate total size of directory in bytes
        
        Args:
            path: Directory path
            
        Returns:
            Total size in bytes
        """
        total = 0
        try:
            if not os.path.exists(path):
                return 0
                
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        if os.path.exists(filepath):
                            total += os.path.getsize(filepath)
                    except (OSError, PermissionError):
                        pass
        except Exception:
            pass
        return total
    
    def get_current_stats(self) -> Dict:
        """Get current resource usage statistics"""
        memory_info = self.process.memory_info()
        ram_mb = memory_info.rss / 1024 / 1024
        disk_mb = self._get_directory_size(self.data_dir) / 1024 / 1024
        
        return {
            'current_ram_mb': ram_mb,
            'current_disk_mb': disk_mb,
            'peak_ram_mb': self.peak_ram_mb,
            'peak_disk_mb': self.peak_disk_mb
        }
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics for the entire monitoring period
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.samples:
            return {
                'peak_ram_mb': 0,
                'average_ram_mb': 0,
                'peak_disk_mb': 0,
                'average_disk_mb': 0,
                'final_disk_mb': 0,
                'total_monitoring_time_seconds': 0,
                'sample_count': 0
            }
        
        ram_values = [s['ram_mb'] for s in self.samples]
        disk_values = [s['disk_mb'] for s in self.samples]
        
        total_time = self.samples[-1]['elapsed_seconds'] if self.samples else 0
        
        return {
            'peak_ram_mb': max(ram_values),
            'average_ram_mb': sum(ram_values) / len(ram_values),
            'peak_disk_mb': max(disk_values),
            'average_disk_mb': sum(disk_values) / len(disk_values),
            'final_disk_mb': disk_values[-1] if disk_values else 0,
            'total_monitoring_time_seconds': total_time,
            'sample_count': len(self.samples)
        }
    
    def save_time_series(self, output_path: str):
        """
        Save time series data for plotting
        
        Args:
            output_path: Path to save JSON file
        """
        data = {
            'samples': self.samples,
            'summary': self.get_summary_stats(),
            'metadata': {
                'data_directory': self.data_dir,
                'sampling_interval_seconds': self.interval,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None
            }
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Saved time series metrics to {output_path}")
    
    def save_csv_for_plotting(self, output_path: str):
        """
        Save metrics in CSV format suitable for plotting
        
        Args:
            output_path: Path to save CSV file
        """
        import csv
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['elapsed_seconds', 'ram_mb', 'disk_mb'])
            
            for sample in self.samples:
                writer.writerow([
                    sample['elapsed_seconds'],
                    sample['ram_mb'],
                    sample['disk_mb']
                ])
        
        print(f"💾 Saved CSV metrics to {output_path}")


class PaperMetrics:
    """
    Tracks per-paper metrics and statistics (thread-safe with checkpoint support)
    """
    
    def __init__(self, checkpoint_dir: str = "./metrics"):
        self.papers: List[Dict] = []
        self.start_time: Optional[float] = None
        self.entry_discovery_time: float = 0
        self._lock = threading.Lock()  # Thread-safety lock
        
        # Checkpoint support
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.checkpoint_path = os.path.join(checkpoint_dir, "paper_metrics_checkpoint.json")
        self.autosave_thread: Optional[threading.Thread] = None
        self.autosaving = False
        
    def load_checkpoint(self) -> bool:
        """
        Load paper metrics from checkpoint file (for resume after Colab disconnect)
        
        Returns:
            bool: True if checkpoint was loaded successfully
        """
        if not os.path.exists(self.checkpoint_path):
            print("📂 No paper metrics checkpoint found - starting fresh")
            return False
        
        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with self._lock:
                self.papers = data.get('papers', [])
                self.start_time = data.get('start_time')
                self.entry_discovery_time = data.get('entry_discovery_time', 0)
            
            print(f"✅ Loaded paper metrics checkpoint with {len(self.papers)} papers")
            return True
            
        except Exception as e:
            print(f"⚠️  Failed to load paper metrics checkpoint: {e}")
            return False
    
    def save_checkpoint(self):
        """Save current paper metrics to checkpoint file (thread-safe)"""
        try:
            with self._lock:
                data = {
                    'papers': self.papers,
                    'start_time': self.start_time,
                    'entry_discovery_time': self.entry_discovery_time,
                    'last_saved': time.time()
                }
            
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Failed to save paper metrics checkpoint: {e}")
    
    def _autosave_loop(self, interval: float = 30.0):
        """
        Background thread to auto-save paper metrics periodically
        
        Args:
            interval: Save interval in seconds (default: 30s)
        """
        while self.autosaving:
            time.sleep(interval)
            if self.autosaving:  # Check again after sleep
                self.save_checkpoint()
                with self._lock:
                    paper_count = len(self.papers)
                print(f"💾 Auto-saved paper metrics checkpoint ({paper_count} papers)")
    
    def start_autosave(self, interval: float = 30.0):
        """
        Start auto-save thread for paper metrics
        
        Args:
            interval: Save interval in seconds (default: 30s)
        """
        if self.autosaving:
            return
        
        self.autosaving = True
        self.autosave_thread = threading.Thread(
            target=self._autosave_loop,
            args=(interval,),
            daemon=True
        )
        self.autosave_thread.start()
        print(f"📊 Started paper metrics auto-save ({interval}s interval)")
    
    def stop_autosave(self):
        """Stop auto-save thread and save final checkpoint"""
        if not self.autosaving:
            return
        
        self.autosaving = False
        if self.autosave_thread:
            self.autosave_thread.join(timeout=2.0)
        
        # Final save
        self.save_checkpoint()
        print("📊 Stopped paper metrics auto-save (final checkpoint saved)")
        
    def start_timing(self):
        """Start overall timing"""
        self.start_time = time.time()
        
    def set_entry_discovery_time(self, duration: float):
        """Set time taken for entry discovery phase"""
        self.entry_discovery_time = duration
        
    def add_paper(self, paper_id: str, success: bool, process_time: float, 
                  size_before: int = 0, size_after: int = 0, 
                  num_references: int = 0, num_versions: int = 0,
                  reference_fetch_success: bool = False, no_tex_source: bool = False):
        """
        Add metrics for a processed paper (thread-safe)
        
        Args:
            paper_id: ArXiv paper ID
            success: Whether processing was successful
            process_time: Time taken to process (seconds)
            size_before: Size in bytes before removing figures
            size_after: Size in bytes after removing figures
            num_references: Number of references found
            num_versions: Number of versions processed
            reference_fetch_success: Whether references were successfully fetched from Semantic Scholar
            no_tex_source: Whether paper has no LaTeX source (PDF-only)
        """
        with self._lock:
            self.papers.append({
                'paper_id': paper_id,
                'success': success,
                'process_time_seconds': process_time,
                'size_before_bytes': size_before,
                'size_after_bytes': size_after,
                'num_references': num_references,
                'num_versions': num_versions,
                'reference_fetch_success': reference_fetch_success,
                'no_tex_source': no_tex_source,
                'timestamp': time.time()
            })
    
    def get_statistics(self) -> Dict:
        """
        Calculate statistics from collected paper metrics (thread-safe)
        
        Returns:
            Dictionary with various statistics
        """
        with self._lock:
            if not self.papers:
                return {
                    'total_papers': 0,
                    'successful_papers': 0,
                    'failed_papers': 0,
                    'success_rate': 0,
                    'average_process_time_seconds': 0,
                    'total_process_time_seconds': 0,
                    'average_size_before_bytes': 0,
                    'average_size_after_bytes': 0,
                    'average_references_per_paper': 0,
                    'total_references': 0,
                    'entry_discovery_time_seconds': self.entry_discovery_time
                }
            
            successful = [p for p in self.papers if p['success']]
            failed = [p for p in self.papers if not p['success']]
        
        # Calculate statistics
        total_papers = len(self.papers)
        num_successful = len(successful)
        num_failed = len(failed)
        success_rate = num_successful / total_papers if total_papers > 0 else 0
        
        # Time statistics
        process_times = [p['process_time_seconds'] for p in self.papers]
        avg_process_time = sum(process_times) / len(process_times)
        total_process_time = sum(process_times)
        
        # Size statistics (only for successful papers)
        sizes_before = [p['size_before_bytes'] for p in successful if p['size_before_bytes'] > 0]
        sizes_after = [p['size_after_bytes'] for p in successful if p['size_after_bytes'] > 0]
        
        avg_size_before = sum(sizes_before) / len(sizes_before) if sizes_before else 0
        avg_size_after = sum(sizes_after) / len(sizes_after) if sizes_after else 0
        
        # Reference statistics
        ref_counts = [p['num_references'] for p in successful]
        avg_references = sum(ref_counts) / len(ref_counts) if ref_counts else 0
        total_references = sum(ref_counts)
        
        # No TeX source statistics
        no_tex_count = len([p for p in self.papers if p.get('no_tex_source', False)])
        no_tex_rate = no_tex_count / total_papers if total_papers > 0 else 0
        
        # Total wall time
        total_wall_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'total_papers_attempted': total_papers,
            'successful_papers': num_successful,
            'failed_papers': num_failed,
            'success_rate': success_rate,
            'success_rate_percentage': success_rate * 100,
            
            # Time statistics
            'average_time_per_paper_seconds': avg_process_time,
            'total_processing_time_seconds': total_process_time,
            'total_wall_time_seconds': total_wall_time,
            'entry_discovery_time_seconds': self.entry_discovery_time,
            
            # Size statistics
            'average_size_before_bytes': avg_size_before,
            'average_size_after_bytes': avg_size_after,
            'average_size_before_mb': avg_size_before / 1024 / 1024,
            'average_size_after_mb': avg_size_after / 1024 / 1024,
            
            # Reference statistics
            'average_references_per_paper': avg_references,
            'total_references_found': total_references,
            
            # Reference scraping success rate
            'papers_with_references': len([p for p in successful if p['num_references'] > 0]),
            'reference_success_rate': len([p for p in successful if p['num_references'] > 0]) / num_successful if num_successful > 0 else 0,
            'reference_success_rate_percentage': (len([p for p in successful if p['num_references'] > 0]) / num_successful * 100) if num_successful > 0 else 0,
            
            # Reference fetch from Semantic Scholar success rate (regardless of arXiv refs)
            'papers_with_reference_fetch_success': len([p for p in successful if p.get('reference_fetch_success', False)]),
            'reference_fetch_success_rate': len([p for p in successful if p.get('reference_fetch_success', False)]) / num_successful if num_successful > 0 else 0,
            'reference_fetch_success_rate_percentage': (len([p for p in successful if p.get('reference_fetch_success', False)]) / num_successful * 100) if num_successful > 0 else 0,
            
            # No TeX source statistics (PDF-only papers)
            'papers_with_no_tex_source': no_tex_count,
            'no_tex_source_rate': no_tex_rate,
            'no_tex_source_rate_percentage': no_tex_rate * 100
        }
    
    def save_per_paper_csv(self, output_path: str):
        """Save per-paper metrics to CSV file (thread-safe)"""
        import csv
        
        with self._lock:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if not self.papers:
                    return
                    
                writer = csv.DictWriter(f, fieldnames=self.papers[0].keys())
                writer.writeheader()
                writer.writerows(self.papers)
        
        print(f"💾 Saved per-paper metrics to {output_path}")
    
    def save_statistics_json(self, output_path: str):
        """Save statistics summary to JSON file"""
        stats = self.get_statistics()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        print(f"💾 Saved statistics to {output_path}")
