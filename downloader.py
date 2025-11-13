"""
Downloader Module
Handles downloading and extracting LaTeX source files from arXiv
"""
import requests
import tarfile
import gzip
import struct
import os
import time
from arxiv_client import format_arxiv_id, get_latest_version
from metadata_collector import build_metadata_and_refs_optimized


def download_and_extract_tex_bib(arxiv_id, version, base_save_dir="./downloads", keep_exts=("tex", "bib")):
    """
    Download and extract .tex/.bib files for a specific version
    
    Args:
        arxiv_id: ArXiv ID without version
        version: Version number
        base_save_dir: Base directory to save files
        keep_exts: Tuple of file extensions to keep
        
    Returns:
        tuple: (success, size_before, size_after) where sizes are in bytes
    """
    full_id = f"{arxiv_id}v{version}"
    safe_id = format_arxiv_id(arxiv_id)
    temp_path = os.path.join(base_save_dir, f"{full_id}.tmp")
    full_id_safe = format_arxiv_id(full_id)
    save_dir = os.path.join(base_save_dir, safe_id, "tex", full_id_safe)
    os.makedirs(save_dir, exist_ok=True)
    
    size_before = 0
    size_after = 0

    size_before = 0
    size_after = 0

    try:
        source_url = f"https://arxiv.org/e-print/{full_id}"
        r = requests.get(source_url)
        if r.status_code != 200:
            print(f"⚠️  No source found for {full_id}")
            return False, 0, 0

        # Save temporary file
        with open(temp_path, "wb") as f:
            f.write(r.content)

        # Determine file type and extract accordingly
        extracted_files = []
        try:
            # Case 1: Try opening as tar.gz archive (multiple files)
            with tarfile.open(temp_path, "r:gz") as tar:
                # Calculate size_before (all files in archive)
                for member in tar.getmembers():
                    if member.isfile():
                        size_before += member.size
                
                # Extract only .tex/.bib files
                for member in tar.getmembers():
                    if not member.isfile():
                        continue

                    filename = os.path.basename(member.name)
                    ext = filename.split(".")[-1].lower()

                    if ext in keep_exts:
                        target_path = os.path.join(save_dir, member.name)
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        with tar.extractfile(member) as src, open(target_path, "wb") as dst:
                            dst.write(src.read())
                        extracted_files.append(target_path)
                        size_after += member.size
                
                print(f"✅ Extracted .tex/.bib from tar.gz for {full_id}")
        except tarfile.ReadError:
            # Case 2: Might be a single gzipped file
            try:
                with gzip.open(temp_path, 'rb') as gz:
                    # Read content
                    content = gz.read()
                    size_before = len(content)
                    
                    # Try to get filename from gzip header
                    gz.seek(0)
                    filename = None
                    try:
                        # Gzip header may contain original filename
                        gz.seek(3)  # Skip magic number and method
                        flags = struct.unpack('B', gz.read(1))[0]
                        gz.seek(10)  # Skip to filename if FNAME flag is set
                        if flags & 0x08:  # FNAME flag
                            filename_bytes = b''
                            while True:
                                byte = gz.read(1)
                                if byte == b'\x00':
                                    break
                                filename_bytes += byte
                            filename = filename_bytes.decode('latin-1')
                    except:
                        pass
                    
                    # If no filename in header, use default name
                    if not filename:
                        filename = f"{full_id_safe}.tex"
                    else:
                        # Normalize filename to use yymm-id format
                        # Example: 2412.05287v1.tex -> 2412-05287v1.tex
                        filename_base = os.path.splitext(filename)[0]
                        filename_ext = os.path.splitext(filename)[1]
                        if '.' in filename_base and not filename_base.startswith('.'):
                            filename_base = filename_base.replace('.', '-', 1)
                        filename = filename_base + filename_ext
                    
                    # Check extension
                    ext = filename.split(".")[-1].lower()
                    if ext in keep_exts:
                        output_path = os.path.join(save_dir, filename)
                        with open(output_path, 'wb') as out:
                            out.write(content)
                        extracted_files.append(output_path)
                        size_after = len(content)
                        print(f"✅ Extracted single file {filename} for {full_id}")
                    else:
                        print(f"⚠️  Single file with ext .{ext} (not in {keep_exts})")
                        return False, 0, 0
            except Exception as e2:
                # Case 3: Might be PDF or other format
                content_type = r.headers.get('Content-Type', '')
                if 'pdf' in content_type.lower():
                    print(f"⚠️  Source is PDF (no LaTeX available) for {full_id}")
                else:
                    print(f"⚠️  Unknown format for {full_id}: {e2}")
                return False, 0, 0

        os.remove(temp_path)
        return True, size_before, size_after

    except Exception as e:
        print(f"❌ Error {full_id}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False, 0, 0


def download_paper(arxiv_id, config, config_path="config.json", collect_metrics=False):
    """
    Download all versions and metadata for a single paper
    
    Args:
        arxiv_id: ArXiv ID without version
        config: Configuration dictionary
        config_path: Path to config file (for progress tracking)
        collect_metrics: Whether to collect and return metrics
        
    Returns:
        tuple: (success, metrics_dict) if collect_metrics=True, else bool
    """
    settings = config["download_settings"]
    safe_id = format_arxiv_id(arxiv_id)
    paper_dir = os.path.join(settings["base_dir"], safe_id)
    
    # Initialize metrics
    metrics = {
        'size_before': 0,
        'size_after': 0,
        'num_references': 0,
        'num_versions': 0,
        'reference_fetch_success': False
    }
    
    try:
        # Get latest version
        latest_v = get_latest_version(arxiv_id)
        if latest_v == 0:
            raise ValueError(f"Paper {arxiv_id} not found.")
        print(f"\n🔍 {arxiv_id}: found {latest_v} versions")
        
        metrics['num_versions'] = latest_v
        
        # Download all versions and accumulate sizes
        total_size_before = 0
        total_size_after = 0
        
        for v in range(1, latest_v + 1):
            success, size_before, size_after = download_and_extract_tex_bib(
                arxiv_id, 
                v, 
                base_save_dir=settings["base_dir"],
                keep_exts=tuple(settings["keep_extensions"])
            )
            if success:
                total_size_before += size_before
                total_size_after += size_after
                print(f"   Version {v}: {size_before} bytes before → {size_after} bytes after")
            else:
                print(f"⚠️  Skipping version {v}")
            time.sleep(settings["delay_between_versions"])
        
        metrics['size_before'] = total_size_before
        metrics['size_after'] = total_size_after
        print(f"📊 Total for {arxiv_id}: {total_size_before} bytes before → {total_size_after} bytes after")
        
        # Download metadata and references
        print(f"📥 Downloading metadata and references for {arxiv_id}...")
        metadata = build_metadata_and_refs_optimized(arxiv_id, output_dir=settings["base_dir"])
        
        # Count references and check if fetch was successful
        if metadata and 'references' in metadata:
            metrics['num_references'] = len(metadata['references'])
        
        # Check if reference fetch was successful (all_references_count > 0)
        if metadata and metadata.get('all_references_count', 0) > 0:
            metrics['reference_fetch_success'] = True
        
        # Mark as completed
        if safe_id not in config["progress"]["completed_papers"]:
            config["progress"]["completed_papers"].append(safe_id)
        
        if collect_metrics:
            return True, metrics
        return True
        
    except Exception as e:
        print(f"❌ Failed to process {arxiv_id}: {e}")
        if safe_id not in config["progress"]["failed_papers"]:
            config["progress"]["failed_papers"].append(safe_id)
        
        if collect_metrics:
            return False, metrics
        return False


def _get_directory_size(path):
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
