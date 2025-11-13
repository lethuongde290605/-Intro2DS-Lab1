# ArXiv Downloader - Refactored Structure

## 📁 Project Structure

```
src/
├── __init__.py              # Package initialization and exports
├── main.py                  # Main entry point for batch downloading
├── config_manager.py        # Configuration loading and saving
├── arxiv_client.py          # ArXiv API and web scraping functions
├── metadata_collector.py    # Metadata and references collection from Semantic Scholar
├── downloader.py            # Download and extraction functions
└── utils.py                 # Common utility functions
```

## 📝 Module Description

### `config_manager.py`
Handles configuration management:
- `load_config()` - Load configuration from JSON file
- `save_config()` - Save configuration to JSON file

### `arxiv_client.py`
ArXiv API interactions:
- `format_arxiv_id()` - Convert arxiv_id format (dot to dash)
- `get_latest_version()` - Get latest version number of a paper
- `get_arxiv_version_dates()` - Scrape version dates from arXiv webpage

### `metadata_collector.py`
Metadata and references collection:
- `get_semantic_scholar_data()` - Fetch data from Semantic Scholar API
- `get_metadata_and_references_optimized()` - Get metadata and references efficiently
- `build_metadata_and_refs_optimized()` - Create metadata.json and references.json

### `downloader.py`
Download and extraction operations:
- `safe_extract_selected()` - Extract specific file types from tarball
- `download_and_extract_tex_bib()` - Download and extract LaTeX source files
- `download_paper()` - Download all versions and metadata for a paper

### `utils.py`
Common utilities:
- `save_json()` - Save object as JSON file

### `main.py`
Main execution script with batch download logic and progress tracking.

## 🚀 Usage

### Run the batch downloader:
```bash
python -m src.main
```

### Use as a library:
```python
from src import download_paper, load_config

config = load_config("config.json")
download_paper("1706.03762", config)
```

### Import specific functions:
```python
from src.metadata_collector import build_metadata_and_refs_optimized

build_metadata_and_refs_optimized("1706.03762", "./data")
```

## 🔧 Benefits of This Structure

1. **Modularity**: Each module has a clear, single responsibility
2. **Maintainability**: Easy to find and modify specific functionality
3. **Reusability**: Functions can be imported and used independently
4. **Testability**: Each module can be tested in isolation
5. **Readability**: Clean code with proper documentation
6. **Extensibility**: Easy to add new features without affecting existing code

## 📦 Dependencies

All dependencies remain the same as before:
- arxiv
- requests
- beautifulsoup4
- tarfile (built-in)
- json (built-in)

## ⚠️ Migration Note

The old `main.py` and `libs.py` files are still present in the root directory for backward compatibility. You can safely remove them once you've verified the new structure works correctly.
