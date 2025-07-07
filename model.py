from MMR import LTRC_manager
from imagegen import LTRCImageGenerator
import os
from datetime import datetime

class LTRCModel:
    def __init__(self):
        self.LTRC = LTRC_manager()

    def set_mode(self, mode):
        self.LTRC.mode = mode

    def toggle_32track(self, enabled):
        self.LTRC.flag_32track = enabled

    def get_table_data(self):
        self.LTRC.LTRC_routine()

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

    def update_sheet(self):
        self.LTRC.update_placements_MMR()
        self.LTRC.update_sheet()
        self.LTRC.clear_table()
        
    def generate_image(self, subtitle, progress_callback=None):
        """
        Generate an image with the tournament results
        
        Args:
            subtitle: Text to display as subtitle
            progress_callback: Function to call with progress updates
            
        Returns:
            str: Path to the saved image
        """
        # Create the image generator with the current format
        generator = LTRCImageGenerator(self.LTRC.mode, progress_callback)
        
        # Get the player results from LTRC
        results = self.LTRC.get_results()
        print(results)
        # Generate the image
        img = generator.generate(results, subtitle)
        
        # Create an 'images' directory if it doesn't exist
        os.makedirs('images', exist_ok=True)
        
        # Save the image with a timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tournament_{self.LTRC.mode}_{timestamp}.png"
        filepath = os.path.join('images', filename)
        img.save(filepath)
        
        # Return the full path to the saved image
        return os.path.abspath(filepath)