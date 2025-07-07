from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QPushButton, QComboBox, QCheckBox, 
                            QWidget, QTableWidget, QTableWidgetItem, QHBoxLayout, QLabel, 
                            QHeaderView, QLineEdit, QProgressBar, QScrollArea)
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QPixmap, QImage, QResizeEvent
import os

class LTRCView(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LTRC Manager v0.4.1")
        self.resize(800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.start_button = QPushButton("Start")
        self.dropdown = QComboBox()
        self.dropdown.addItems(["FFA", "2vs2", "3vs3", "4vs4", "5vs5", "6vs6"])
        self.checkbox = QCheckBox("32 track")
        
        # Initialize the image generation flag
        self.image_generated = False
        self.image_path = None

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
        
        # Reset the image generation flag and path
        self.image_generated = False
        self.image_path = None

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
        racers, scores, MMRs, deltas, new_MMRs = table_data

        # Create a table
        self.table = QTableWidget(len(racers), 5, self)

        # Disable resizing of the table's columns and rows
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # Set the headers of the table
        self.table.setHorizontalHeaderLabels(["Player", "Score", "MMR", "Change", "New Rating"])  # Set the header labels


        # Fill the table with data
        for i in range(len(racers)):
            self.table.setItem(i, 0, QTableWidgetItem(racers[i]))
            self.table.setItem(i, 1, QTableWidgetItem(scores[i]))
            self.table.setItem(i, 2, QTableWidgetItem(MMRs[i]))
            self.table.setItem(i, 3, QTableWidgetItem(deltas[i]))
            self.table.setItem(i, 4, QTableWidgetItem(new_MMRs[i]))
            
            # Set the flags for the items
            for j in range(5):
                self.table.item(i, j).setFlags(Qt.ItemFlag.ItemIsSelectable)

        # Add the table to the layout
        self.layout.addWidget(self.table)

        # Add the text to the layout
        self.text = QLabel("Check if the data is correct.\nPress continue to write the table on the sheet.", self)
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
     
    def show_image_gen_screen(self):
        # Create a widget to hold the text, input field, and buttons
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)

        # Create the header text
        self.header_text = QLabel("Image Generation", self)
        self.header_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.header_text)

        # Create subtitle input field
        subtitle_layout = QHBoxLayout()
        subtitle_label = QLabel("Subtitle for image:", self)
        self.subtitle_input = QLineEdit(self)
        self.subtitle_input.setPlaceholderText("Enter event name or description")
        subtitle_layout.addWidget(subtitle_label)
        subtitle_layout.addWidget(self.subtitle_input)
        self.layout.addLayout(subtitle_layout)

        # Add some spacing
        self.layout.addSpacing(20)

        # Create explanatory text
        self.image_info_text = QLabel(
            "You can generate an image with the tournament results.\n"
            "The subtitle will be displayed below the title on the image.", 
            self
        )
        self.image_info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_info_text)

        # Add buttons
        self.skip_button = QPushButton("Skip Image Generation", self)
        self.generate_button = QPushButton("Generate Image", self)
        self.discord_button = QPushButton("Generate and upload to Discord", self)

        # Add buttons to layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.skip_button)
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.discord_button)
        self.layout.addLayout(button_layout)

        # Set the widget as the central widget
        self.setCentralWidget(self.widget)

    def show_image_progress_screen(self):
        # Create a widget to hold the progress bar and status text
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)

        # Create the header text
        self.header_text = QLabel("Generating Image...", self)
        self.header_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.header_text)

        # Create progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.layout.addWidget(self.progress_bar)

        # Create status text
        self.status_text = QLabel("Starting image generation...", self)
        self.status_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_text)

        # Set the widget as the central widget
        self.setCentralWidget(self.widget)

    def update_progress(self, value, message=None):
        """Update the progress bar and status message"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)
            
        if hasattr(self, 'status_text') and message:
            self.status_text.setText(message)
     
    def show_write_screen(self):
        # Create a widget to hold the text and button
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)
        
        # Check if an image has been generated using the flag
        if self.image_generated and hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            # Create an image display area
            self.image_label = QLabel(self)
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Create a scroll area for the image
            self.scroll_area = QScrollArea()
            self.scroll_area.setWidget(self.image_label)
            self.scroll_area.setWidgetResizable(True)
            self.layout.addWidget(self.scroll_area)
            
            # Scale the image initially
            self.scale_image()
            
            # Connect resize event to image scaling function
            self.resizeEvent = self.on_resize
            
            # Add image action buttons
            button_layout = QHBoxLayout()
            
            # Add "Copy to Clipboard" button
            self.copy_button = QPushButton("Copy Image to Clipboard", self)
            button_layout.addWidget(self.copy_button)
            
            # Add "Save Image" button
            self.save_button = QPushButton("Save Image", self)
            button_layout.addWidget(self.save_button)
            
            self.layout.addLayout(button_layout)
            
            # Add label asking if the user wants to write MMR values
            self.final_text = QLabel("\nWrite new MMR values to the sheet?", self)
            self.final_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.final_text)
        else:
            # Create the text for screenshot reminder
            self.final_text = QLabel("Make the table screenshot before continuing!\n\nWrite new MMR values to the sheet?", self)
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
    
    def scale_image(self):
        """Scale the image to fit the current window size while maintaining aspect ratio"""
        if hasattr(self, 'original_pixmap') and hasattr(self, 'image_label') and hasattr(self, 'scroll_area'):
            # Get the available size in the scroll area
            available_width = self.scroll_area.width() - 20  # Subtract some padding
            available_height = self.scroll_area.height() - 20  # Subtract some padding
            
            # Scale the pixmap to fit within the available space while preserving aspect ratio
            scaled_pixmap = self.original_pixmap.scaled(
                available_width, 
                available_height,
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Update the image label with the scaled pixmap
            self.image_label.setPixmap(scaled_pixmap)

    def on_resize(self, event: QResizeEvent):
        """Handle window resize events"""
        # Scale the image when the window is resized
        if hasattr(self, 'original_pixmap'):
            self.scale_image()
        
        # Call the parent class's resizeEvent
        super().resizeEvent(event)

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