from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView, QLabel, QHBoxLayout, QVBoxLayout, QComboBox, QMessageBox, QCheckBox
from PyQt6.QtCore import Qt, QCoreApplication
import sys
import traceback

from MMR import LTRC_manager
from settings import load_settings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # init the LTRC communication class
        self.LTRC = LTRC_comms()

        # Set window properties
        self.setWindowTitle("LTRC Manager")

        # Resize the window
        self.resize(800, 600)

        # Show the start screen
        self.show_start_screen()

    def show_start_screen(self):
        # Create a layout
        layout = QVBoxLayout()

        # Create a start button
        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.show_table_screen)

        # Create a dropdown menu
        self.dropdown = QComboBox(self)
        self.dropdown.addItems(["FFA", "2vs2", "3vs3", "4vs4", "5vs5", "6vs6"])

        # Create a checkbox
        self.checkbox = QCheckBox("32 track", self)
        self.checkbox.toggled.connect(self.LTRC.handle_32track)

        # Add the start button and dropdown menu to the layout
        layout.addWidget(self.dropdown)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.start_button)

        # Create a widget to hold the layout
        widget = QWidget()
        widget.setLayout(layout)

        # Set the widget as the central widget
        self.setCentralWidget(widget)

    def show_table_screen(self):
        # Get the currently selected value from the dropdown menu
        self.LTRC.LTRC.mode = self.dropdown.currentText()

        # Create a widget to hold the table, text, and buttons
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)

        # Get the data for the table
        racers, scores, MMRs, deltas, new_MMRs, accolades = self.LTRC.get_table()

        # Create a table
        self.table = QTableWidget(len(racers), 7, self)

        # Disable resizing of the table's columns and rows
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # Set the headers of the table
        self.table.setHorizontalHeaderLabels(["Player","Score", "MMR", "Change", "New Rating", "Accolades", "Bonus Acc."])  # Set the header labels


        # Fill the table with data
        for i in range(len(racers)):
            self.table.setItem(i, 0, QTableWidgetItem(racers[i]))
            self.table.setItem(i, 1, QTableWidgetItem(scores[i]))
            self.table.setItem(i, 2, QTableWidgetItem(MMRs[i]))
            self.table.setItem(i, 3, QTableWidgetItem(deltas[i]))
            self.table.setItem(i, 4, QTableWidgetItem(new_MMRs[i]))
            self.table.setItem(i, 5, QTableWidgetItem(accolades[i]))
            
            # Set the flags for the items
            for j in range(6):
                self.table.item(i, j).setFlags(Qt.ItemFlag.ItemIsSelectable)

            # Add an editable item to the last column
            item = QTableWidgetItem('')
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)  # Set the ItemIsEditable flag
            self.table.setItem(i, 6, item)

        # Initialize a list to store the user input
        self.bonus_accolades = ['' for _ in range(12)]

        # Connect the cellChanged signal to the user_input_changed method
        self.table.cellChanged.connect(self.user_input_changed)
        
        # Add the table to the layout
        self.layout.addWidget(self.table)

        # Add the text to the layout
        self.text = QLabel("Check if the data is correct.\nAdd bonus accolades in the final column. Accolade penalties are negative.\nPress continue to write the table on the sheet.", self)
        self.layout.addWidget(self.text)

        # Create a horizontal layout for the buttons
        self.button_layout = QHBoxLayout()

        # Create the "Refresh" button
        self.refresh_button = QPushButton("Refresh", self)
        self.refresh_button.clicked.connect(self.show_table_screen)

        # Create the "Continue" button
        self.continue_button = QPushButton("Continue", self)
        self.continue_button.clicked.connect(self.show_write_screen)

        # Add the "No" and "Yes" buttons to the layout
        self.button_layout.addWidget(self.refresh_button)
        self.button_layout.addWidget(self.continue_button)

        # Add the button layout to the main layout
        self.layout.addLayout(self.button_layout)

        # Set the widget as the central widget
        self.setCentralWidget(self.widget)

    def user_input_changed(self, row, column):
    # If the changed cell is in the last column (the "User Input" column)
        if column == 6:
            # Update the user_input list with the new text
            self.bonus_accolades[row] = self.table.item(row, column).text()
            
    def show_write_screen(self):
        # Write the table
        self.LTRC.write_table(self.bonus_accolades)

        # Create a widget to hold the final text and button
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)

        # Create the final text
        self.final_text = QLabel(f"Make the table screenshot before continuing!\n Write new MMR and accolades values to the sheet?", self)
        self.layout.addWidget(self.final_text)

        # Create the "Close" button
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(QCoreApplication.quit)

        # Add the "Close" button to the layout
        self.layout.addWidget(self.close_button)

        # Create the "Write" button
        self.write_button = QPushButton("Write", self)
        self.write_button.clicked.connect(self.write_to_sheet)

        # Add the "Write" button to the layout
        self.layout.addWidget(self.write_button)

        # Set the widget as the central widget
        self.setCentralWidget(self.widget)

    def write_to_sheet(self):

        # Create a text widget
        self.text = QLabel("Updating the sheet...", self)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Update the sheet
        self.LTRC.update_sheet()

        # Close the application
        QCoreApplication.quit()

class LTRC_comms:
    def __init__(self):
        self.LTRC = LTRC_manager()
        pass

    def handle_32track(self, checked):
        self.LTRC.flag_32track = checked

    def get_table(self):
        self.LTRC.LTRC_routine()

        racers = self.LTRC.racers
        scores = [f"{score}" for score in self.LTRC.scores]
        MMRs = [f"{MMR}" for MMR in self.LTRC.MMRs]

        deltas = [f"{delta}" for delta in self.LTRC.delta_MMRs]
        accolades = [f"{accolade}" for accolade in self.LTRC.accolades]
        new_MMRs = [f"{MMR}" for MMR in self.LTRC.MMR_new]

        return racers, scores, MMRs, deltas, new_MMRs, accolades

    def write_table(self, bonus_accolades):
        # Convert the bonus accolades to integers
        bonus_accolades = [int(accolade) if accolade else 0 for accolade in bonus_accolades]

        # Add the bonus accolades to the accolades
        for i in range(len(self.LTRC.accolades)):
            self.LTRC.accolades[i] += bonus_accolades[i]

        # Write the data to the table
        self.LTRC.fill_MMR_change_table()
        self.LTRC.fill_accolades_table()

    def update_sheet(self):
        self.LTRC.update_placements_MMR()
        self.LTRC.update_sheet()
        self.LTRC.clear_table()

def main_function():
    # Load the settings
    settings = load_settings() 

    # Create a Qt application
    app = QApplication(sys.argv)

    # Open the sqq styles file and read in the CSS-alike styling code
    with open(settings['style'], 'r') as f:
        style = f.read()
        # Set the stylesheet of the application
        app.setStyleSheet(style)

    # Create and show the main window
    window = MainWindow()
    window.show()

    # Run the application
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

if __name__ == "__main__":
    sys.excepthook = handle_exception

    main_function()