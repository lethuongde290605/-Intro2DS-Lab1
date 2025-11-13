#!/usr/bin/env python3
"""
ArXiv Batch Downloader with Progress Tracking
Main entry point for the application
"""
import time
from config_manager import load_config, save_config
from arxiv_client import format_arxiv_id, get_latest_version
from downloader import download_paper


def main():
    """Main execution function for batch downloading arXiv papers"""
    config_path = "config.json"
    
    # Load config
    config = load_config(config_path)
    progress = config["progress"]
    settings = config["download_settings"]
    
    print("=" * 80)
    print("🚀 ArXiv Batch Downloader with Progress Tracking")
    print("=" * 80)
    print(f"📁 Output directory: {settings['base_dir']}")
    print(f"📊 Range: {progress['prefix']}.{progress['start']:05d} to {progress['prefix']}.{progress['end']:05d}")
    print(f"📈 Current progress: {progress['current']}")
    print(f"✅ Completed: {len(progress['completed_papers'])} papers")
    print(f"❌ Failed: {len(progress['failed_papers'])} papers")
    print("=" * 80)
    
    # Resume from last position
    start_from = progress["current"]
    
    try:
        for i in range(start_from, progress["end"] + 1):
            arxiv_id = f"{progress['prefix']}.{i:05d}"
            safe_id = format_arxiv_id(arxiv_id)
            
            # Skip if already completed
            if safe_id in progress["completed_papers"]:
                print(f"⏭️  Skipping {arxiv_id} (already completed)")
                continue
            
            # Update current position
            progress["current"] = i
            
            # Download paper
            print(f"\n{'='*80}")
            print(f"📄 Processing {i - start_from + 1}/{progress['end'] - start_from + 1}: {arxiv_id}")
            print(f"{'='*80}")
            
            success = download_paper(arxiv_id, config, config_path)
            
            # Save progress after each paper
            save_config(config, config_path)
            
            # Delay between papers
            if success:
                time.sleep(settings["delay_between_papers"])
            else:
                print(f"⚠️  Will retry {arxiv_id} later if needed")
                time.sleep(settings["delay_between_papers"] * 2)
        
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


if __name__ == "__main__":
    main()
