"""
ArXiv Client Module
Handles interactions with arXiv API and web scraping
"""
import arxiv
import requests
import re
from bs4 import BeautifulSoup


def format_arxiv_id(arxiv_id):
    """
    Convert arxiv_id to format yymm-id (without dot)
    Example: '1706.03762' -> '1706-03762'
    
    Args:
        arxiv_id: ArXiv ID with dot
        
    Returns:
        str: ArXiv ID with dash
    """
    return arxiv_id.replace('.', '-')


def get_latest_version(arxiv_id):
    """
    Get the latest version number for a paper
    Example: Returns 7 for '1706.03762v7'
    
    Args:
        arxiv_id: ArXiv ID without version
        
    Returns:
        int: Latest version number, or 0 if not found
    """
    try:
        search = arxiv.Search(id_list=[arxiv_id])
        paper = next(arxiv.Client().results(search))
        match = re.search(r"v(\d+)$", paper.entry_id)
        return int(match.group(1)) if match else 1
    except StopIteration:
        print(f"❌ Paper {arxiv_id} not found in arXiv.")
        return 0


def get_arxiv_version_dates(arxiv_id):
    """
    Scrape all version submission dates from arXiv webpage
    
    Args:
        arxiv_id: ArXiv ID
        
    Returns:
        list: List of date strings in YYYY-MM-DD format
    """
    url = f"https://arxiv.org/abs/{arxiv_id}"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find submission history section
    version_div = soup.find('div', {'class': 'submission-history'})
    revised_dates = []

    if version_div:
        version_text = version_div.get_text()
        # Pattern: Mon, 12 Jun 2017 17:57:34 UTC
        date_pattern = r'[A-Z][a-z]{2},\s+(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{4})\s+\d{2}:\d{2}:\d{2}\s+UTC'
        matches = re.findall(date_pattern, version_text)
        
        # Convert to YYYY-MM-DD
        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }
        
        for day, month, year in matches:
            month_num = month_map.get(month, '01')
            day_str = day.zfill(2)
            date_iso = f"{year}-{month_num}-{day_str}"
            revised_dates.append(date_iso)
    
    return revised_dates
