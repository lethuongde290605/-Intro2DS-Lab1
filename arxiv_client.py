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

def get_arxiv_metadata(arxiv_id):
    """
    Lấy chung metadata từ arXiv: title, authors, latest version, submission date, revised_dates
    """
    url = f"https://arxiv.org/abs/{arxiv_id}"
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Lấy title
    paper_title_tag = soup.find('h1', {'class': 'title'})
    paper_title = paper_title_tag.text.replace('Title:', '').strip() if paper_title_tag else ""

    # Lấy authors
    authors_tag = soup.find('div', {'class': 'authors'})
    authors = []
    if authors_tag:
        authors = [a.strip() for a in authors_tag.text.replace('Authors:', '').split(',')]

    # Lấy version history
    version_div = soup.find('div', {'class': 'submission-history'})
    revised_dates = []
    latest_version = 1
    submission_date = None

    if version_div:
        version_text = version_div.get_text()
        # Pattern: Mon, 12 Jun 2017 17:57:34 UTC
        date_pattern = r'[A-Z][a-z]{2},\s+(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{4})\s+\d{2}:\d{2}:\d{2}\s+UTC'
        matches = re.findall(date_pattern, version_text)
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
        if revised_dates:
            submission_date = revised_dates[0]
            latest_version = len(revised_dates)

    return {
        "paper_title": paper_title,
        "authors": authors,
        "revised_dates": revised_dates,
        "submission_date": submission_date,
        "latest_version": latest_version
    }