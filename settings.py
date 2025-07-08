import json
import os
import sys

def get_base_path():
    """Get the base path for resource files, works for both development and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        base_path = sys._MEIPASS
    else:
        # Running as a regular Python script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return base_path

def load_settings():
    """Load settings from config.json file"""
    try:
        # Get the correct path to config.json
        config_path = os.path.join(get_base_path(), "config.json")
        print(f"Loading config from: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Ensure paths in config are absolute
        if 'style' in config:
            config['style'] = os.path.join(get_base_path(), config['style'])
        
        # Extract just the needed settings for the application
        settings_dict = {
            'sheetname': config.get('sheetname', 'LTRC Manager MMR calculator'),
            'style': config.get('style', os.path.join(get_base_path(), 'style.qss'))
        }
        
        return settings_dict
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading settings: {e}")
        raise RuntimeError(f"Failed to load settings. Please check config.json file at {os.path.join(get_base_path(), 'config.json')}")
