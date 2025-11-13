"""
Utilities Module
Common helper functions used across the application
"""
import json


def save_json(obj, path):
    """
    Save object as JSON file
    
    Args:
        obj: Object to save (must be JSON serializable)
        path: File path to save to
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)
