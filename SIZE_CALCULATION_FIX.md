# Size Calculation Fix - Summary

## Problem
Previously, the code was measuring:
- `size_before`: Size of paper directory before download
- `size_after`: Size of paper directory after download

This was incorrect because it didn't properly track the size reduction from filtering out non-.tex/.bib files.

## Solution
Now the code correctly measures size **per version**:

### For Each Version (v1, v2, v3, etc.):
1. **Download** the tar.gz/gz file from arXiv
2. **Extract ALL files** to a temporary directory
3. **Measure `size_before_v`**: Total size of all extracted files (including figures, PDFs, etc.)
4. **Filter and copy** only .tex and .bib files to final destination
5. **Measure `size_after_v`**: Total size of only .tex/.bib files
6. **Clean up** temporary directory

### For Each Paper (with multiple versions):
- `size_before = sum(size_before_v1, size_before_v2, ..., size_before_vN)`
- `size_after = sum(size_after_v1, size_after_v2, ..., size_after_vN)`

This gives us:
- **Accurate size reduction**: Shows how much space we saved by filtering
- **Per-version tracking**: Each version's contribution is measured separately
- **Correct totals**: Sum of all versions gives the paper's total size

## Example
If a paper has 2 versions:
- v1: size_before = 10 MB (includes figures), size_after = 100 KB (only .tex/.bib)
- v2: size_before = 12 MB (includes figures), size_after = 120 KB (only .tex/.bib)

Then the paper totals:
- `size_before = 22 MB`
- `size_after = 220 KB`
- `reduction = 21.78 MB (99% reduction)`

## Code Changes
1. **`downloader.py`**:
   - `download_and_extract_tex_bib()` now returns `(success, size_before, size_after)` tuple
   - Uses temporary directory to extract all files first
   - Measures size before filtering
   - Copies only .tex/.bib files to final destination
   - Measures size after filtering
   
2. **`download_paper()`**:
   - Accumulates `size_before` and `size_after` from all versions
   - Returns correct totals in metrics

## Files Modified
- `downloader.py`: Fixed size calculation logic
- `METRICS_README.md`: Updated documentation
- `test_size_calculation.py`: New test script to verify the fix

## Testing
Run the test script:
```bash
python3 test_size_calculation.py
```

This will:
1. Download a test paper with multiple versions
2. Calculate size_before and size_after correctly
3. Show the reduction percentage
4. Save results to `test_size_results.json`
