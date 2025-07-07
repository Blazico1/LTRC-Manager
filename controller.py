from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
import os
from datetime import datetime

class ImageGeneratorThread(QThread):
    # Define signals for progress updates and completion
    progress_updated = pyqtSignal(int, str)
    image_generated = pyqtSignal(str)
    
    def __init__(self, model, subtitle):
        super().__init__()
        self.model = model
        self.subtitle = subtitle
        
    def run(self):
        # Generate the image and get the path
        def progress_callback(value, message):
            self.progress_updated.emit(value, message)
            
        image_path = self.model.generate_image(self.subtitle, progress_callback)
        self.image_generated.emit(image_path)

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
        self.view.continue_button.clicked.connect(self.show_image_gen_screen)
    
    def show_image_gen_screen(self):
        self.view.show_image_gen_screen()
        
        # Connect the buttons to their respective actions
        self.view.skip_button.clicked.connect(self.show_write_screen)
        self.view.generate_button.clicked.connect(self.start_image_generation)
        self.view.discord_button.clicked.connect(self.start_image_generation_with_discord)
    
    def start_image_generation(self):
        # Get the subtitle from the input field
        subtitle = self.view.subtitle_input.text()
        
        # Show the progress screen
        self.view.show_image_progress_screen()
        
        # Create and start a worker thread for image generation
        self.image_thread = ImageGeneratorThread(self.model, subtitle)
        self.image_thread.progress_updated.connect(self.view.update_progress)
        self.image_thread.image_generated.connect(self.on_image_generated)
        self.image_thread.start()
    
    def start_image_generation_with_discord(self):
        # This would be similar to start_image_generation but with additional discord upload
        subtitle = self.view.subtitle_input.text()
        self.view.show_image_progress_screen()
        
        # For now, just do the same as regular image generation
        # In the future, this would also handle Discord upload
        self.image_thread = ImageGeneratorThread(self.model, subtitle)
        self.image_thread.progress_updated.connect(self.view.update_progress)
        self.image_thread.image_generated.connect(self.on_image_generated_with_discord)
        self.image_thread.start()
    
    def on_image_generated(self, image_path):
        # Store the image path in the view for display in the end screen
        self.view.image_path = image_path
        self.view.image_generated = True
        
        # Continue to the write screen after image generation
        self.show_write_screen()
    
    def on_image_generated_with_discord(self, image_path):
        # Store the image path in the view
        self.view.image_path = image_path
        self.view.image_generated = True
        
        # Here we would handle Discord upload
        # For now, just show a message in the progress screen
        self.view.update_progress(100, "Discord upload would happen here (not yet implemented)")
        QTimer.singleShot(2000, self.show_write_screen)

    def show_write_screen(self):
        self.model.write_table()
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
