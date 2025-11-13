"""
Test script to verify size calculation for versions
"""
import sys
import json
from downloader import download_paper
from config_manager import load_config

def test_size_calculation():
    """Test that size_before and size_after are calculated correctly per version"""
    print("=" * 60)
    print("Testing Size Calculation (Before/After per Version)")
    print("=" * 60)
    
    # Load config
    config = load_config("config.json")
    
    # Test with a paper (using one from your list)
    test_arxiv_id = "2412.05292"  # This one exists in your data folder
    
    print(f"\n📝 Testing with arXiv ID: {test_arxiv_id}")
    print("-" * 60)
    
    # Download and collect metrics
    success, metrics = download_paper(
        test_arxiv_id, 
        config, 
        config_path="config.json",
        collect_metrics=True
    )
    
    if success:
        print("\n✅ Download successful!")
        print("\n📊 Metrics collected:")
        print(f"  • Number of versions: {metrics['num_versions']}")
        print(f"  • Size before (all extracted files): {metrics['size_before']:,} bytes ({metrics['size_before'] / 1024:.2f} KB)")
        print(f"  • Size after (only .tex/.bib): {metrics['size_after']:,} bytes ({metrics['size_after'] / 1024:.2f} KB)")
        print(f"  • Reduction: {metrics['size_before'] - metrics['size_after']:,} bytes ({(1 - metrics['size_after']/metrics['size_before'])*100:.2f}%)")
        print(f"  • Number of references: {metrics['num_references']}")
        
        # Save test results
        with open('test_size_results.json', 'w') as f:
            json.dump(metrics, f, indent=2)
        print("\n💾 Results saved to test_size_results.json")
    else:
        print("\n❌ Download failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = test_size_calculation()
    sys.exit(0 if success else 1)
