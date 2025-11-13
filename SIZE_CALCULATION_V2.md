# Size Calculation Methodology

## Overview
This document explains how file sizes are calculated for arXiv papers with multiple versions.

## Calculation Logic

### Per-Version Calculation
For each version `v_i` of an arXiv paper:

1. **Size Before (`size_before_vi`)**: 
   - When downloading the source archive (`.tar.gz` or single `.gz` file)
   - This represents the total size of ALL files in the archive before filtering
   - For `.tar.gz` archives: Sum of all member file sizes
   - For single `.gz` files: Size of the decompressed content

2. **Size After (`size_after_vi`)**:
   - After extracting and keeping only `.tex` and `.bib` files
   - This represents the size of only the LaTeX source files
   - For `.tar.gz` archives: Sum of sizes of extracted `.tex` and `.bib` files
   - For single `.gz` files: Size of the file if it's `.tex` or `.bib`, 0 otherwise

### Per-Paper Aggregation
For a paper with versions `v_1, v_2, ..., v_n`:

```
size_before_paper = Σ size_before_vi  (sum over all versions i=1 to n)
size_after_paper  = Σ size_after_vi   (sum over all versions i=1 to n)
```

## Implementation Details

### Function: `download_and_extract_tex_bib()`
Returns: `(success, size_before, size_after)` tuple for a single version

**Case 1: Multi-file tar.gz archive**
```python
size_before = sum(member.size for all members)
size_after = sum(member.size for .tex/.bib members only)
```

**Case 2: Single gzipped file**
```python
content = decompress(file)
size_before = len(content)
if file_extension in ['tex', 'bib']:
    size_after = len(content)
else:
    size_after = 0
```

### Function: `download_paper()`
Accumulates sizes across all versions:
```python
total_size_before = 0
total_size_after = 0

for each version v:
    success, size_before, size_after = download_and_extract_tex_bib(...)
    if success:
        total_size_before += size_before
        total_size_after += size_after
```

## Example

Consider paper `2412.05292` with 3 versions:

| Version | Files in Archive | size_before | Files Kept | size_after |
|---------|------------------|-------------|------------|------------|
| v1      | main.tex, fig1.png, fig2.jpg, refs.bib | 1,500,000 | main.tex, refs.bib | 50,000 |
| v2      | main.tex, fig1.png, fig2.jpg, fig3.pdf, refs.bib | 2,000,000 | main.tex, refs.bib | 55,000 |
| v3      | main.tex, fig1.png, fig2.jpg, fig3.pdf, fig4.png, refs.bib | 2,500,000 | main.tex, refs.bib | 60,000 |

**Total for paper:**
- `size_before = 1,500,000 + 2,000,000 + 2,500,000 = 6,000,000 bytes`
- `size_after = 50,000 + 55,000 + 60,000 = 165,000 bytes`
- `Size reduction = (1 - 165,000/6,000,000) × 100% = 97.25%`

## Verification

To verify the calculation is correct:
1. `size_after` should always be ≤ `size_before` (we're filtering out files)
2. Typical reduction rate is 80-99% (figures are usually much larger than text)
3. Papers with only `.tex` files will have minimal reduction
4. Papers with many figures/images will have high reduction

## Testing

Run the test script to verify:
```bash
python test_size_calculation_v2.py
```

This will:
- Download a multi-version paper
- Print size for each version
- Show total sizes and reduction percentage
- Verify that `size_after ≤ size_before`
