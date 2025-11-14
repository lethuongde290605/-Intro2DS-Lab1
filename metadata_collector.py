"""
Metadata Collector Module
Handles fetching metadata and references from Semantic Scholar and arXiv
"""
import arxiv
import requests
import time
from utils import save_json
import os
import threading

semantic_scholar_lock = threading.Lock()


def get_semantic_scholar_data(arxiv_id, api_key=None):
    """
    Fetch ALL information from Semantic Scholar in a single API call
    
    Args:
        arxiv_id: ArXiv ID
        api_key: Semantic Scholar API key (optional)
        
    Returns:
        tuple: (publication_venue, references_dict)
    """
    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}"
    params = {
        "fields": "venue,journal,publicationVenue,"
                  "references,references.externalIds,references.title,"
                  "references.authors,references.publicationDate,references.paperId"
    }
    headers = {
        "x-api-key": api_key
    } if api_key else {}

    publication_venue = ""
    refs = {}
    max_attempt = 50
    all_references_count = 0
    
    for attempt in range(max_attempt):
        try:

            with semantic_scholar_lock:
                r = requests.get(url, params=params, headers=headers, timeout=15)
                time.sleep(1)

            if r.status_code == 429:
                print(f"⚠️ Rate limit hit (attempt {attempt+1}/{max_attempt})")
                continue
            
            r.raise_for_status()
            data = r.json()
            
            # Extract publication venue
            pub_venue = data.get("publicationVenue")
            if pub_venue and isinstance(pub_venue, dict):
                publication_venue = pub_venue.get("name", "")
            if not publication_venue:
                publication_venue = data.get("venue", "")
            if not publication_venue:
                journal = data.get("journal")
                if journal and isinstance(journal, dict):
                    publication_venue = journal.get("name", "")
            
            all_references_count = len(data.get("references", []))
            # Extract references
            for ref in data.get("references", []):
                arxiv_ref_id = (ref.get("externalIds") or {}).get("ArXiv")
                if not arxiv_ref_id:
                    continue
                
                key = arxiv_ref_id.replace(".", "-")
                refs[key] = {
                    "paper_title": ref.get("title", "").strip(),
                    "authors": [a.get("name") for a in ref.get("authors", []) if "name" in a],
                    "submission_date": ref.get("publicationDate"),
                    "semantic_scholar_id": ref.get("paperId")
                }
            
            print(f"✅ Successfully fetched Semantic Scholar data on attempt {attempt+1}")
            break
            
        except Exception as e:
            print(f"⚠️ Error on attempt {attempt+1}: {e}")
            if attempt == max_attempt - 1:
                print(f"❌ Failed to fetch Semantic Scholar data after {max_attempt} attempts")
                break
    
    return publication_venue, refs, all_references_count


def build_metadata_and_refs(arxiv_id, arxiv_metadata, output_dir="./data", api_key=None):
    """
    Create metadata.json and references.json for a paper
    Optimized version: uses pre-fetched arxiv_metadata
    
    Args:
        arxiv_id: ArXiv ID
        arxiv_metadata: Pre-fetched metadata from arXiv (from get_arxiv_metadata)
        output_dir: Output directory for data
        api_key: Semantic Scholar API key (optional)
        
    Returns:
        dict: Combined metadata including references and reference fetch info
    """
    print(f"\n{'='*60}")
    print(f"📄 Building metadata for: {arxiv_id}")
    print(f"{'='*60}")
    
    safe_id = arxiv_id.replace(".", "-")
    paper_dir = os.path.join(output_dir, safe_id)
    os.makedirs(paper_dir, exist_ok=True)

    # Get venue + references from Semantic Scholar
    print("🔍 Fetching venue + references from Semantic Scholar...")
    publication_venue, references, all_references_count = get_semantic_scholar_data(arxiv_id, api_key)
    
    # Use arxiv_metadata if venue is empty
    if not publication_venue:
        publication_venue = ""  # ArXiv doesn't always have venue info
    
    # Build metadata using arxiv_metadata
    metadata = {
        "paper_title": arxiv_metadata.get("paper_title", ""),
        "authors": arxiv_metadata.get("authors", []),
        "publication_venue": publication_venue,
        "submission_date": arxiv_metadata.get("submission_date", ""),
        "revised_dates": arxiv_metadata.get("revised_dates", []),
    }
    
    # Save files
    metadata_path = os.path.join(paper_dir, "metadata.json")
    references_path = os.path.join(paper_dir, "references.json")
    
    save_json(metadata, metadata_path)
    save_json(references, references_path)

    print(f"\n📊 Results:")
    print(f"  - Title: {metadata['paper_title']}")
    print(f"  - Authors: {len(metadata['authors'])} authors")
    print(f"  - Venue: {publication_venue or '(empty)'}")
    print(f"  - Versions: {len(metadata['revised_dates'])} versions")
    print(f"  - Total references from Semantic Scholar: {all_references_count}")
    print(f"  - ArXiv references: {len(references)} arXiv references")

    print(f"\n✅ Files saved:")
    print(f"  - {metadata_path}")
    print(f"  - {references_path}")
    
    # Return combined data for metrics
    return {
        **metadata,
        'references': references,
        'all_references_count': all_references_count,
    }