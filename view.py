from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QComboBox, QCheckBox, QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout, QLabel, QHeaderView
from PyQt6.QtCore import Qt, QCoreApplication

class LTRCView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LTRC Manager")
        self.resize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.start_button = QPushButton("Start")
        self.dropdown = QComboBox()
        self.dropdown.addItems(["FFA", "2vs2", "3vs3", "4vs4", "5vs5", "6vs6"])
        self.checkbox = QCheckBox("32 track")

        self.layout.addWidget(self.dropdown)
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.start_button)

    def restart(self):
        # Clear the existing layout
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.start_button = QPushButton("Start")
        self.dropdown = QComboBox()
        self.dropdown.addItems(["FFA", "2vs2", "3vs3", "4vs4", "5vs5", "6vs6"])
        self.checkbox = QCheckBox("32 track")

        self.layout.addWidget(self.dropdown)
        self.layout.addWidget(self.checkbox)
        self.layout.addWidget(self.start_button)

    def show_table_screen(self, table_data):
        # Clear the existing layout
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Create a widget to hold the table, text, and buttons
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)

        # Get the data for the table
        racers, scores, MMRs, deltas, new_MMRs, accolades = table_data

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

        # Create the "Continue" button
        self.continue_button = QPushButton("Continue", self)

        # Add the buttons to the layout
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

        # Create a widget to hold the text and button
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)

        # Create the text
        self.final_text = QLabel(f"Make the table screenshot before continuing!\n\nWrite new MMR and accolades values to the sheet?", self)
        self.layout.addWidget(self.final_text)

        # Create the "Close" button
        self.close_button = QPushButton("Close", self)
        self.close_button.clicked.connect(QCoreApplication.quit)

        # Add the "Close" button to the layout
        self.layout.addWidget(self.close_button)

        # Create the "Write" button
        self.write_button = QPushButton("Write", self)

        # Add the "Write" button to the layout
        self.layout.addWidget(self.write_button)

        # Set the widget as the central widget
        self.setCentralWidget(self.widget)

    def show_write_loading(self):
        # Create a widget to hold the text
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)

        # Create a text widget
        self.text = QLabel("Updating the sheet...", self)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.text)

        # Set the widget as the central widget
        self.setCentralWidget(self.widget)

    def show_end_screen(self):
        # Create a widget to hold the text
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)

        # Create a text widget
        self.text = QLabel("Sheet updated successfully! Do you want to run the program again?", self)
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.text)

        # Create buttons
        self.restart_button = QPushButton("Restart", self)
        self.close_button = QPushButton("Close", self)

        self.close_button.clicked.connect(self.close)

        # Create horizontal layout for the buttons
        self.button_layout = QHBoxLayout()

        # Add the buttons to the layout
        self.button_layout.addWidget(self.restart_button)
        self.button_layout.addWidget(self.close_button)

        # Add the button layout to the main layout
        self.layout.addLayout(self.button_layout)

        # Set the widget as the central widget
        self.setCentralWidget(self.widget)

    def close(self):
        QCoreApplication.quit()