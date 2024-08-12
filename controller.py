from PyQt6.QtCore import QTimer

class LTRCController:
    def __init__(self, model, view):
        self.model = model
        self.view = view

        self.view.start_button.clicked.connect(self.show_table_screen)
        self.view.checkbox.toggled.connect(self.toggle_32track)

    def restart(self):
        self.view.restart()
        self.view.start_button.clicked.connect(self.show_table_screen)
        self.view.checkbox.toggled.connect(self.toggle_32track)

    def show_table_screen(self):
        mode = self.view.dropdown.currentText()
        self.model.set_mode(mode)
        table_data = self.model.get_table_data()
        self.view.show_table_screen(table_data)

        self.view.refresh_button.clicked.connect(self.restart)
        self.view.continue_button.clicked.connect(self.show_write_screen)
    
    def show_write_screen(self):
        self.model.write_table(self.view.bonus_accolades)
        self.view.show_write_screen()
        self.view.write_button.clicked.connect(self.show_write_loading)

    def show_write_loading(self):
        self.view.show_write_loading()
        QTimer.singleShot(100, self.show_end_screen)

    def show_end_screen(self):
        self.model.update_sheet()
        self.view.show_end_screen()
        self.view.restart_button.clicked.connect(self.restart)

    def toggle_32track(self, enabled):
        self.model.toggle_32track(enabled)
