from MMR import LTRC_manager
from imagegen import LTRCImageGenerator
import os
from datetime import datetime
from PIL import Image
from io import BytesIO
import json
import sys

class LTRCModel:
    def __init__(self):
        self.LTRC = LTRC_manager()
        self.generated_image = None

    def set_mode(self, mode):
        self.LTRC.mode = mode

    def toggle_32track(self, enabled):
        self.LTRC.flag_32track = enabled

    def get_table_data(self, progress_callback=None):
        """
        Retrieves table data with progress updates
        
        Args:
            progress_callback: Optional function to report loading progress
        
        Returns:
            Tuple containing racers, scores, MMRs, deltas, new_MMRs
        """
        # Pass the progress callback to the LTRC routine
        self.LTRC.LTRC_routine(progress_callback)

        racers = self.LTRC.racers
        scores = [f"{score}" for score in self.LTRC.scores]
        MMRs = [f"{MMR}" for MMR in self.LTRC.MMRs]

        deltas = [f"{delta}" for delta in self.LTRC.delta_MMRs]
        new_MMRs = [f"{MMR}" for MMR in self.LTRC.MMR_new]
        
        return racers, scores, MMRs, deltas, new_MMRs

    def write_table(self):
        # Write the data to the table
        self.LTRC.fill_MMR_change_table()
        self.LTRC.fill_rank_change_table()

    def update_sheet(self, progress_callback=None):
        """
        Update the sheet with detailed progress tracking
        
        Args:
            progress_callback: Optional callback function for progress updates
        """
        # Pass the progress callback to the LTRC manager for detailed updates
        self.LTRC.update_placements_MMR(progress_callback)
        self.LTRC.update_sheet(progress_callback)
        self.LTRC.clear_table(progress_callback)
        
    def generate_image(self, subtitle, progress_callback=None):
        """
        Generate an image with the tournament results
        
        Args:
            subtitle: Text to display as subtitle
            progress_callback: Function to call with progress updates
            
        Returns:
            PIL.Image: The generated image
        """
        # Load the image generator config
        try:
            # Get the correct base path that works with PyInstaller
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
                
            config_path = os.path.join(base_path, "config.json")
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update file paths in the config to be absolute
            if 'font_file' in config:
                config['font_file'] = os.path.join(base_path, config['font_file'])
            
            if 'background_image' in config:
                config['background_image'] = os.path.join(base_path, config['background_image'])
            
            # Ensure the rank_icons folder path is absolute
            config['rank_icons_dir'] = os.path.join(base_path, 'rank_icons')

        except Exception as e:
            raise RuntimeError(f"Failed to load image generator config from {config_path}")
        
        # Create the image generator with the current format and required config
        generator = LTRCImageGenerator(
            self.LTRC.mode,
            config,
            progress_callback=progress_callback
        )
        
        # Get the player results from LTRC
        results = self.LTRC.get_results()
        
        # Generate the image
        self.generated_image = generator.generate(results, subtitle)
        
        # Return the image object
        return self.generated_image
    
    def save_image_to_file(self, filename=None):
        """
        Save the generated image to a file if needed
        
        Args:
            filename: Optional custom filename, otherwise auto-generated
            
        Returns:
            str: Path to the saved image or None if no image was generated
        """
        if self.generated_image is None:
            return None
            
        # Create an 'images' directory if it doesn't exist
        os.makedirs('images', exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"tournament_{self.LTRC.mode}_{timestamp}.png"
        
        # Ensure filename has .png extension
        if not filename.lower().endswith('.png'):
            filename += '.png'
            
        filepath = os.path.join('images', filename)
        self.generated_image.save(filepath)
        
        # Return the full path to the saved image
        return os.path.abspath(filepath)