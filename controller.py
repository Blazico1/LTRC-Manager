from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap, QClipboard
from PyQt6.QtWidgets import QApplication, QFileDialog
import os
from datetime import datetime
from PIL.ImageQt import ImageQt

class ImageGeneratorThread(QThread):
    # Define signals for progress updates and completion
    progress_updated = pyqtSignal(int, str)
    image_generated = pyqtSignal(object)  # Now passing the PIL image directly
    
    def __init__(self, model, subtitle):
        super().__init__()
        self.model = model
        self.subtitle = subtitle
        
    def run(self):
        # Generate the image and get the PIL image object
        def progress_callback(value, message):
            self.progress_updated.emit(value, message)
            
        pil_image = self.model.generate_image(self.subtitle, progress_callback)
        self.image_generated.emit(pil_image)

class SheetUpdateThread(QThread):
    # Define signals for progress updates and completion
    progress_updated = pyqtSignal(int, str)
    update_completed = pyqtSignal()
    
    def __init__(self, model):
        super().__init__()
        self.model = model
        
    def run(self):
        # Define a progress callback function to pass to the update_sheet method
        def progress_callback(value, message):
            self.progress_updated.emit(value, message)
            
        # Update the sheet with progress tracking
        self.model.update_sheet(progress_callback)
        self.update_completed.emit()

class TableDataThread(QThread):
    # Define signals for progress updates and completion
    progress_updated = pyqtSignal(int, str)
    data_loaded = pyqtSignal(object)
    
    def __init__(self, model, mode):
        super().__init__()
        self.model = model
        self.mode = mode
        
    def run(self):
        # Define a progress callback function to pass to the get_table_data method
        def progress_callback(value, message):
            self.progress_updated.emit(value, message)
            
        # Set the mode first
        self.model.set_mode(self.mode)
        
        # Get table data with progress tracking
        table_data = self.model.get_table_data(progress_callback)
        
        # Signal that data is loaded
        self.data_loaded.emit(table_data)

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
        
        # Show loading screen
        self.view.show_loading_screen(f"Loading {mode} Tournament Data...")
        
        # Create and start a worker thread for data loading
        self.data_thread = TableDataThread(self.model, mode)
        self.data_thread.progress_updated.connect(self.view.update_progress)
        self.data_thread.data_loaded.connect(self.on_data_loaded)
        self.data_thread.start()
    
    def on_data_loaded(self, table_data):
        # Show the table screen with the loaded data
        self.view.show_table_screen(table_data)
        
        # Connect buttons for the table screen
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
        pass
    
    def on_image_generated(self, pil_image):
        # Store the PIL image in the view for display and clipboard operations
        self.view.pil_image = pil_image
        self.view.image_generated = True
        
        # Convert PIL image to QPixmap for display
        q_image = ImageQt(pil_image)
        self.view.original_pixmap = QPixmap.fromImage(q_image)
        
        # Continue to the write screen after image generation
        self.show_write_screen()

    def copy_image_to_clipboard(self):
        """Copy the generated image to clipboard"""
        if hasattr(self.view, 'original_pixmap') and not self.view.original_pixmap.isNull():
            # Copy the QPixmap directly to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setPixmap(self.view.original_pixmap)
            
            # Update the button text to provide feedback
            self.view.copy_button.setText("Image Copied to Clipboard!")
            
            # Reset the button text after 2 seconds
            QTimer.singleShot(2000, lambda: self.view.copy_button.setText("Copy Image to Clipboard"))

    def save_image(self):
        """Save the generated image to a file"""
        if hasattr(self.view, 'pil_image') and self.view.pil_image:
            # Open a file dialog for the user to choose where to save the image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_name = f"tournament_{self.model.LTRC.mode}_{timestamp}.png"
            
            # Use current working directory instead of creating an images directory
            filepath, _ = QFileDialog.getSaveFileName(
                self.view, 
                "Save Image", 
                os.path.join(os.getcwd(), default_name),
                "PNG Files (*.png);;All Files (*)"
            )
            
            if filepath:
                # Save the image directly without creating any directories
                self.view.pil_image.save(filepath)
                
                # Update save button text to provide feedback
                self.view.save_button.setText("Image Saved!")
                
                # Reset the button text after 2 seconds
                QTimer.singleShot(2000, lambda: self.view.save_button.setText("Save Image"))

    def show_write_screen(self):
        self.model.write_table()
        self.view.show_write_screen()
        
        # Connect the buttons
        self.view.write_button.clicked.connect(self.show_write_loading)
        
        # Connect the image-related buttons if image was generated
        if self.view.image_generated:
            if hasattr(self.view, 'copy_button'):
                self.view.copy_button.clicked.connect(self.copy_image_to_clipboard)
            if hasattr(self.view, 'save_button'):
                self.view.save_button.clicked.connect(self.save_image)

    def show_write_loading(self):
        # Show the write loading screen with progress bar
        self.view.show_write_loading()
        
        # Create and start a worker thread for sheet updating
        self.update_thread = SheetUpdateThread(self.model)
        self.update_thread.progress_updated.connect(self.view.update_progress)
        self.update_thread.update_completed.connect(self.show_end_screen)
        self.update_thread.start()

    def show_end_screen(self):
        self.model.update_sheet()
        self.view.show_end_screen()
        self.view.restart_button.clicked.connect(self.restart)

    def toggle_32track(self, enabled):
        self.model.toggle_32track(enabled)
        self.view.save_button.setText("Image Saved!")
        
        # Reset the button text after 2 seconds
        QTimer.singleShot(2000, lambda: self.view.save_button.setText("Save Image"))

    def show_write_screen(self):
        self.model.write_table()
        self.view.show_write_screen()
        
        # Connect the buttons
        self.view.write_button.clicked.connect(self.show_write_loading)
        
        # Connect the image-related buttons if image was generated
        if self.view.image_generated:
            if hasattr(self.view, 'copy_button'):
                self.view.copy_button.clicked.connect(self.copy_image_to_clipboard)
            if hasattr(self.view, 'save_button'):
                self.view.save_button.clicked.connect(self.save_image)

    def show_write_loading(self):
        # Show the write loading screen with progress bar
        self.view.show_write_loading()
        
        # Create and start a worker thread for sheet updating
        self.update_thread = SheetUpdateThread(self.model)
        self.update_thread.progress_updated.connect(self.view.update_progress)
        self.update_thread.update_completed.connect(self.show_end_screen)
        self.update_thread.start()

    def show_end_screen(self):
        self.model.update_sheet()
        self.view.show_end_screen()
        self.view.restart_button.clicked.connect(self.restart)

    def toggle_32track(self, enabled):
        self.model.toggle_32track(enabled)
    def show_write_loading(self):
        # Show the write loading screen with progress bar
        self.view.show_write_loading()
        
        # Create and start a worker thread for sheet updating
        self.update_thread = SheetUpdateThread(self.model)
        self.update_thread.progress_updated.connect(self.view.update_progress)
        self.update_thread.update_completed.connect(self.show_end_screen)
        self.update_thread.start()

    def show_end_screen(self):
        self.model.update_sheet()
        self.view.show_end_screen()
        self.view.restart_button.clicked.connect(self.restart)

    def toggle_32track(self, enabled):
        self.model.toggle_32track(enabled)
