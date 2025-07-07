import json
import os

def load_settings():
    """Load settings from config.json file"""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Extract just the needed settings for the application
        settings_dict = {
            'sheetname': config.get('sheetname', 'LTRC Manager MMR calculator'),
            'style': config.get('style', 'style.qss')
        }
        
        return settings_dict
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading settings: {e}")
        raise RuntimeError("Failed to load settings. Please check config.json file.")
