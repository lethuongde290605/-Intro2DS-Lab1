"""
Test script to verify size calculation logic
"""
import os
import sys
from downloader import download_paper
from config_manager import load_config

def test_size_calculation():
    """Test size calculation for one paper with multiple versions"""
    
    # Load config
    config = load_config()
    
    # Test with a paper that has multiple versions
    test_arxiv_id = "1706.03762"  # This paper should have multiple versions
    
    print(f"\n{'='*60}")
    print(f"Testing size calculation for paper: {test_arxiv_id}")
    print(f"{'='*60}\n")
    
    # Download and collect metrics
    success, metrics = download_paper(
        test_arxiv_id, 
        config, 
        collect_metrics=True
    )
    
    print(f"\n{'='*60}")
    print("RESULTS:")
    print(f"{'='*60}")
    print(f"Success: {success}")
    print(f"Number of versions: {metrics['num_versions']}")
    print(f"Total size before (all files): {metrics['size_before']:,} bytes ({metrics['size_before']/1024:.2f} KB)")
    print(f"Total size after (.tex/.bib only): {metrics['size_after']:,} bytes ({metrics['size_after']/1024:.2f} KB)")
    print(f"Size reduction: {(1 - metrics['size_after']/metrics['size_before'])*100:.2f}%" if metrics['size_before'] > 0 else "N/A")
    print(f"Number of references: {metrics['num_references']}")
    print(f"{'='*60}\n")
    
    # Verify calculation makes sense
    if metrics['size_before'] > 0 and metrics['size_after'] > 0:
        if metrics['size_after'] <= metrics['size_before']:
            print("✅ Size calculation looks correct (after <= before)")
        else:
            print("❌ ERROR: Size after is greater than size before!")
            return False
    
    return success

if __name__ == "__main__":
    success = test_size_calculation()
    sys.exit(0 if success else 1)
