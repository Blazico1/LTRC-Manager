import sys
import traceback
import os
import json
from PyQt6.QtWidgets import QApplication, QMessageBox

from model import LTRCModel
from view import LTRCView
from controller import LTRCController

def get_base_path():
    """Get the base path for resource files, works for both development and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        base_path = sys._MEIPASS
    else:
        # Running as a regular Python script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return base_path

def load_config():
    """Load configuration from config.json file"""
    try:
        # Get the correct path to config.json
        config_path = os.path.join(get_base_path(), "config.json")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Resolve paths to be absolute
        if 'style' in config:
            config['style'] = os.path.join(get_base_path(), config['style'])
            
        return config
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to load config. Please check config.json file at {os.path.join(get_base_path(), 'config.json')}")

def main():
    app = QApplication(sys.argv)
    config = load_config()

    # Open the QSS style file and read in the CSS-alike styling code
    with open(config['style'], 'r') as f:
        style = f.read()
        # Set the stylesheet of the application
        app.setStyleSheet(style)

    model = LTRCModel()
    view = LTRCView()
    controller = LTRCController(model, view)
    
    view.show()
    sys.exit(app.exec())

def handle_exception(exc_type, exc_value, exc_traceback):
    # Create a message box to show the exception
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setText("Oi mate! You broke my program!")
    msg.setInformativeText(f"{exc_type.__name__}: {exc_value}")
    msg.setDetailedText(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    msg.setWindowTitle("Error")
    
    msg.exec()

if __name__ == '__main__':
    sys.excepthook = handle_exception
    main()