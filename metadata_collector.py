"""
Metadata Collector Module
Handles fetching metadata and references from Semantic Scholar and arXiv
"""
import arxiv
import requests
import time
from arxiv_client import get_arxiv_version_dates
from utils import save_json
import os


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
    max_attempt = 10
    
    for attempt in range(max_attempt):
        try:
            if attempt > 0:
                wait_time = 15
                print(f"⏳ Waiting {wait_time}s before retry (attempt {attempt+1}/{max_attempt})...")
                time.sleep(wait_time)
                
            r = requests.get(url, params=params, headers=headers, timeout=15)

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
    
    return publication_venue, refs


def get_metadata_and_references_optimized(arxiv_id):
    """
    Optimized version: Get metadata and references with only 2 HTTP requests:
    1. Semantic Scholar API (venue + references together)
    2. ArXiv webpage (version history)
    
    Args:
        arxiv_id: ArXiv ID
        
    Returns:
        tuple: (metadata_dict, references_dict)
    """
    print(f"\n{'='*60}")
    print(f"📄 Processing paper: {arxiv_id}")
    print(f"{'='*60}")
    
    # Get basic info from arxiv library
    print("📚 Fetching basic info from arXiv library...")
    search = arxiv.Search(id_list=[arxiv_id])
    paper = next(arxiv.Client().results(search))

    paper_title = paper.title.strip()
    authors = [str(a) for a in paper.authors]
    
    # Call Semantic Scholar API ONCE
    print("🔍 Fetching venue + references from Semantic Scholar (single call)...")
    publication_venue, references = get_semantic_scholar_data(arxiv_id)
    
    # Fallback venue from arxiv if SS doesn't have it
    if not publication_venue:
        publication_venue = getattr(paper, "journal_ref", None) or ""
    
    # Get version dates from ArXiv webpage
    print("📅 Fetching version history from arXiv webpage...")
    revised_dates = get_arxiv_version_dates(arxiv_id)
    
    # Submission date = first version
    submission_date = revised_dates[0] if revised_dates else paper.published.date().isoformat()

    # Create metadata
    metadata = {
        "paper_title": paper_title,
        "authors": authors,
        "publication_venue": publication_venue,
        "submission_date": submission_date,
        "revised_dates": revised_dates,
    }
    
    print(f"\n📊 Results:")
    print(f"  - Title: {paper_title}")
    print(f"  - Authors: {len(authors)} authors")
    print(f"  - Venue: {publication_venue or '(empty)'}")
    print(f"  - Versions: {len(revised_dates)} versions")
    print(f"  - References: {len(references)} arXiv references")
    
    return metadata, references


def build_metadata_and_refs_optimized(arxiv_id, output_dir="./data"):
    """
    Create metadata.json and references.json for a paper
    Optimized version: ONLY CALLS SEMANTIC SCHOLAR API ONCE!
    
    Args:
        arxiv_id: ArXiv ID
        output_dir: Output directory for data
        
    Returns:
        dict: Combined metadata including references
    """
    safe_id = arxiv_id.replace(".", "-")
    paper_dir = os.path.join(output_dir, safe_id)
    os.makedirs(paper_dir, exist_ok=True)

    # Get both metadata and references in one go
    metadata, references = get_metadata_and_references_optimized(arxiv_id)

    # Save files
    metadata_path = os.path.join(paper_dir, "metadata.json")
    references_path = os.path.join(paper_dir, "references.json")
    
    save_json(metadata, metadata_path)
    save_json(references, references_path)

    print(f"\n✅ Files saved:")
    print(f"  - {metadata_path}")
    print(f"  - {references_path}")
    
    # Return combined data for metrics
    return {
        **metadata,
        'references': references
    }
