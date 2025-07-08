import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox

from model import LTRCModel
from view import LTRCView
from controller import LTRCController
from settings import load_settings

def main():
    settings = load_settings()
    
    app = QApplication(sys.argv)

    # Open the sqq styles file and read in the CSS-alike styling code
    with open(settings['style'], 'r') as f:
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