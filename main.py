import sys
from PyQt6.QtWidgets import QApplication
from model import LTRCModel
from view import LTRCView
from controller import LTRCController

def main():
    app = QApplication(sys.argv)
    model = LTRCModel()
    view = LTRCView()
    controller = LTRCController(model, view)
    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()