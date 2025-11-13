"""
Config Management Module
Handles loading and saving configuration files
"""
import json
import os


def load_config(config_path="config.json"):
    """
    Load configuration from JSON file
    
    Args:
        config_path: Path to the config file
        
    Returns:
        dict: Configuration dictionary
    """
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Default config
        return {
            "api_keys": {
                "semantic_scholar": "",
                "arxiv": ""
            },
            "download_settings": {
                "base_dir": "./data",
                "delay_between_papers": 1.0,
                "delay_between_versions": 0.5,
                "retry_attempts": 3,
                "keep_extensions": ["tex", "bib"]
            },
            "progress": {
                "prefix": "2412",
                "start": 5271,
                "end": 10270,
                "current": 5271,
                "completed_papers": [],
                "failed_papers": []
            }
        }


def save_config(config, config_path="config.json"):
    """
    Save configuration to JSON file
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to save the config file
    """
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print(f"💾 Progress saved to {config_path}")
