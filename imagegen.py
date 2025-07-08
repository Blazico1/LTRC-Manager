import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageColor
import requests
from io import BytesIO
import time
import threading

# MMR Ranges
# Tin: 0-1999
# Bronze: 2000-2999
# Silver: 3000-3999
# Gold: 4000-4999
# Emerald: 5000-5999
# Sapphire: 6000-6999
# Ruby: 7000-7999
# Duke: 8000-8999
# Master: 9000-9999
# Grandmaster: 10000-10999
# Monarch: 11000-14999
# Sovereign: 15000+

class LTRCImageGenerator:
    def __init__(self, format_type, config, progress_callback=None):
        """
        Initialize the tournament image generator with a specific format type.
        
        Args:
            format_type: The format of the tournament (e.g., "FFA", "2vs2")
            config: Configuration dictionary for the image generator
            progress_callback: Optional callback function for progress updates
        """
        # Store the provided config
        self.config = config
        
        # Store the format type
        self.format_type = format_type
        
        # Store all commonly used configuration sections as class attributes
        self.width = self.config['width']
        self.height = self.config['height']
        self.font_file = self.config['font_file']
        self.colors = self.config['colors']
        
        # Format specific configurations
        self.format_config = self.config['formats'][self.format_type]
        self.header_config = self.format_config['header']
        self.podium_style = self.format_config['podium_style']
        self.podium_count = self.format_config['podium_count']
        self.team_size = self.format_config['team_size']
        
        # Path to rank icons folder
        self.rank_icons_dir = os.path.join(os.path.dirname(__file__), 'rank_icons')

        # Image cache for faster repeated loading - only caches original images
        self.image_cache = {}
        
        # Progress tracking
        self.progress_callback = progress_callback
        self.total_steps = 0
        self.completed_steps = 0
        self.progress_lock = threading.Lock()
        
        # Create a session for HTTP requests that can be reused
        self.session = requests.Session()
        
        # Configure session for better performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=1
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # Request timeout
        self.request_timeout = 5  # seconds

    def _update_progress(self, increment=1, message=None):
        """
        Update the progress status and call the progress callback if set
        
        Args:
            increment: Amount to increment the progress counter by
            message: Optional message to include with the progress update
        """
        with self.progress_lock:
            self.completed_steps += increment
            progress = 0
            if self.total_steps > 0:
                progress = min(100, int(100 * self.completed_steps / self.total_steps))
            
            if self.progress_callback and callable(self.progress_callback):
                self.progress_callback(progress, message)
    
    def _load_image(self, source, size=None):
        """
        Load an image from URL or local file path
        
        Args:
            source: URL or file path to load the image from
            size: Optional tuple (width, height) to resize the image
            
        Returns:
            PIL.Image: Loaded image or None if failed
        """
        if not source:
            return None
        
        # Check memory cache for original image
        if source in self.image_cache:
            img = self.image_cache[source]
            # Resize if needed
            if size and img.size != size:
                return img.resize(size)
            return img.copy()  # Return a copy to prevent modifications
    
        # Load from URL or file
        try:
            if source.startswith(('http://', 'https://')):
                # Load from URL (only used for Mii images)
                response = self.session.get(source, stream=True, timeout=self.request_timeout)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))
                else:
                    return None
            else:
                # Load from local file
                img = Image.open(source)
        
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Cache the original image in memory
            self.image_cache[source] = img
            
            # Return resized copy if size specified
            if size and img.size != size:
                return img.resize(size)
            return img.copy()
        
        except Exception as e:
            return None

    def _get_rank_icon_path(self, rank):
        """Get the path to a rank icon file"""
        return os.path.join(self.rank_icons_dir, f"{rank}.png")

    def _get_direction_icon_path(self, direction):
        """Get the path to a direction icon file"""
        return os.path.join(self.rank_icons_dir, f"{direction}.png")

    def _create_base_image(self):
        """Create the base image with background"""
        # Check if background image is specified
        try:
            # Try to load the background image
            img = Image.open(self.config['background_image'])
            # Resize to match configured dimensions if needed
            if img.size != (self.width, self.height):
                img = img.resize((self.width, self.height))
        except (FileNotFoundError, IOError):
            # Fall back to background color if image can't be loaded
            img = Image.new('RGBA', (self.width, self.height), 
                            ImageColor.getrgb(self.config['background_color']))
        
        return img

    def _render_header(self, img, subtitle=None):
        """
        Render the header section with title and subtitle
        
        Args:
            img: The PIL image to draw on
            subtitle: Optional custom subtitle text
        """
        draw = ImageDraw.Draw(img)
        
        # === Render title ===
        title_font = ImageFont.truetype(self.font_file, self.header_config['title_size'])
        title_text = f"{self.format_type} Results"
        title_width = draw.textlength(title_text, font=title_font)
        title_x = (self.width - title_width) // 2
        title_y = self.header_config['title_y']
        
        # Draw main title text (without shadow for now)
        draw.text((title_x, title_y), title_text, 
                 fill=self.header_config['title_color'], font=title_font)
        
        # === Render subtitle ===
        subtitle_font = ImageFont.truetype(self.font_file, self.header_config['subtitle_size'])
        subtitle_width = draw.textlength(subtitle, font=subtitle_font)
        subtitle_x = (self.width - subtitle_width) // 2
        subtitle_y = self.header_config['subtitle_y']
        
        # Draw main subtitle text (without shadow for now)
        draw.text((subtitle_x, subtitle_y), subtitle, 
                    fill=self.header_config['subtitle_color'], font=subtitle_font)
        
        return img

    def _draw_mii(self, img, mii_url, x_pos, y_pos, mii_size):
        """
        Draw a player's Mii image at the specified position
        
        Args:
            img: The PIL image to draw on
            mii_url: URL or path to the Mii image
            x_pos: X position to draw the Mii
            y_pos: Y Position to draw the Mii
            mii_size: Size (width and height) of the Mii image
        """
        # Load Mii image with caching
        mii_img = self._load_image(mii_url, (mii_size, mii_size))
        
        # Paste if loaded successfully
        if mii_img:
            # Paste with or without transparency mask
            if mii_img.mode == 'RGBA':
                img.paste(mii_img, (x_pos, y_pos), mii_img)
            else:
                img.paste(mii_img, (x_pos, y_pos))

    def _draw_miis_vertical(self, img, results, team_index, y_pos, center_x):
        """
        Draw Miis vertically alongside player names (for 5v5 and 6v6 formats)
        
        Args:
            img: The PIL image to draw on
            results: List of player results
            team_index: Index of the team in the results list
            y_pos: Starting vertical position
            center_x: Horizontal center position for alignment
            
        Returns:
            None
        """
        # Get Mii configuration
        mii_config = self.podium_style['mii']
        mii_size = mii_config['size']
        team_size = self.team_size
        mii_y_offset = mii_config['y_offset']
        x_offset = mii_config['x_offset']
        mii_vertical_spacing = mii_config['horizontal_spacing']  
        
        # Calculate starting positions
        mii_x = center_x - x_offset  # Use the configured x_offset value
        mii_y_pos = y_pos + mii_y_offset  # Apply the y_offset from config
        
        # For each team member
        for member_idx in range(team_size):
            player_idx = team_index * team_size + member_idx
            if player_idx < len(results):
                player_data = results[player_idx]
                mii_url = player_data["mii"]
                
                # Calculate vertical position for this Mii
                member_y = mii_y_pos + (member_idx * (mii_size + mii_vertical_spacing))
                
                # Draw the Mii - pass the URL directly
                self._draw_mii(img, mii_url, mii_x, member_y, mii_size)

    def _determine_rank_from_mmr(self, mmr):
        """
        Determine the rank based on MMR value
        
        Args:
            mmr: The MMR value
            
        Returns:
            string: The rank name (lowercase for file lookup purposes)
        """
        if mmr < 2000:
            return "tin"
        elif mmr < 3000:
            return "bronze"
        elif mmr < 4000:
            return "silver"
        elif mmr < 5000:
            return "gold"
        elif mmr < 6000:
            return "emerald"
        elif mmr < 7000:
            return "sapphire"
        elif mmr < 8000:
            return "ruby"
        elif mmr < 9000:
            return "duke"
        elif mmr < 10000:
            return "master"
        elif mmr < 11000:
            return "grandmaster"
        elif mmr < 15000:
            return "monarch"
        else:
            return "sovereign"

    def _draw_player_score_line(self, img, player_data, center_x, stats_y, stats_size, horizontal_spacing):
        """
        Draw the complete player score line with all stats and icons
        
        Args:
            img: The PIL image to draw on
            player_data: Player data dictionary with score, mmr_change, etc.
            center_x: X center position for centering the text
            stats_y: Y position for stats
            stats_size: Font size for stats
            horizontal_spacing: Spacing between elements
            
        Returns:
            None
        """
        draw = ImageDraw.Draw(img)
        
        # Extract player stats
        player_score = player_data["score"]
        mmr_change = player_data["mmr_change"]
        new_mmr = player_data["new_mmr"]
        completion = player_data["completion"]
        
        # Determine rank based on MMR
        rank = self._determine_rank_from_mmr(new_mmr)
        
        # Determine rank change by comparing new rank with old rank
        old_mmr = new_mmr - mmr_change
        old_rank = self._determine_rank_from_mmr(old_mmr)
        
        # Determine rank change direction
        if rank == old_rank:
            rank_change = 0
        else:
            rank_change = 1 if new_mmr > old_mmr else -1
        
        # Create stats text
        stats_font = ImageFont.truetype(self.font_file, stats_size)
        name_color = self.colors['positions']['default']  # Default text color
        
        # Format the text components
        separator = " | "
        mmr_prefix = "+" if mmr_change > 0 else ""
        score_text = f"{player_score}"
        mmr_text = f"{mmr_prefix}{mmr_change}"
        
        # If the player is not fully placed, add an asterisk to the MMR
        new_mmr_text = f"{new_mmr}*" if completion in ["1/3", "2/3"] else f"{new_mmr}"
        
        # Calculate MMR color
        mmr_color = self.colors['mmr_up'] if mmr_change >= 0 else self.colors['mmr_down']
        
        # Check if we need to show placement completion instead of rank icons
        if completion in ["1/3", "2/3"]:
            # Player is in placement matches - prepare to show completion text
            placement_text = completion
            placement_color = name_color  # Use same color as name
        else:
            # Player is fully placed - prepare rank change and rank icons
            # Get direction icon path based on rank change
            direction_icon = None
            direction_tint = None
            
            if completion == "3/3":
                direction_path = self._get_direction_icon_path("right")
                direction_tint = None
            elif rank_change > 0:
                direction_path = self._get_direction_icon_path("up")
                direction_tint = self.colors['mmr_up']
            elif rank_change < 0:
                direction_path = self._get_direction_icon_path("down")
                direction_tint = self.colors['mmr_down']
            else:
                direction_path = self._get_direction_icon_path("neutral")
                direction_tint = None
            
            # Load direction icon with caching
            rank_change_icon_size = (stats_size - 5, stats_size - 5)
            direction_icon = self._load_image(direction_path, rank_change_icon_size)
            
            # Get rank icon path and load it
            rank_icon = None
            rank_icon_size = (stats_size, stats_size)
            rank_icon_path = self._get_rank_icon_path(rank)
            rank_icon = self._load_image(rank_icon_path, rank_icon_size)
        
        # Calculate icon sizes
        rank_change_icon_size = (stats_size - 5, stats_size - 5)
        rank_icon_size = (stats_size, stats_size)
        
        # Build stats text to calculate width for centering
        full_stats_text = f"{score_text}{separator}{mmr_text}{separator}{new_mmr_text}"
        full_stats_width = draw.textlength(full_stats_text, font=stats_font)
        
        # Add width of completion text or icon widths
        separator_width = draw.textlength(separator, font=stats_font)
        
        if completion in ["1/3", "2/3"]:
            # Calculate width needed for completion text
            placement_width = draw.textlength(placement_text, font=stats_font)
            icons_width = placement_width
        else:
            # Calculate width needed for icons
            icons_width = 0
            if 'direction_icon' in locals() and direction_icon:
                icons_width += rank_change_icon_size[0] + horizontal_spacing//2
            if 'rank_icon' in locals() and rank_icon:
                icons_width += rank_icon_size[0]
        
        # Center everything
        total_width = full_stats_width + separator_width + icons_width
        stats_x = center_x - total_width//2
        
        # Draw score
        draw.text((stats_x, stats_y), score_text, fill=name_color, font=stats_font)
        stats_x += draw.textlength(score_text, font=stats_font)
        
        # Draw first separator
        draw.text((stats_x, stats_y), separator, fill=name_color, font=stats_font)
        stats_x += draw.textlength(separator, font=stats_font)
        
        # Draw MMR change
        draw.text((stats_x, stats_y), mmr_text, fill=mmr_color, font=stats_font)
        stats_x += draw.textlength(mmr_text, font=stats_font)
        
        # Draw second separator
        draw.text((stats_x, stats_y), separator, fill=name_color, font=stats_font)
        stats_x += draw.textlength(separator, font=stats_font)
        
        # Draw new MMR (with asterisk for placement players)
        draw.text((stats_x, stats_y), new_mmr_text, fill=name_color, font=stats_font)
        stats_x += draw.textlength(new_mmr_text, font=stats_font)
        
        # Draw separator before icons or completion text
        draw.text((stats_x, stats_y), separator, fill=name_color, font=stats_font)
        stats_x += draw.textlength(separator, font=stats_font)
        
        if completion in ["1/3", "2/3"]:
            # Draw completion text instead of icons
            draw.text((stats_x, stats_y), placement_text, fill=placement_color, font=stats_font)
        else:
            # Get icon vertical alignment adjustment from config and scale it with the stats size
            base_icon_y_offset = self.podium_style['icon_y_offset']
            # Scale offset based on the ratio of current size to a reference size (e.g., 40)
            reference_size = 40  # Reference font size for scaling
            icon_y_offset = base_icon_y_offset * (stats_size / reference_size)
            
            # Calculate common vertical position for both icons with configurable and scaled offset
            icons_y = stats_y + (stats_size - rank_change_icon_size[1]) // 2 + int(icon_y_offset)
            
            # Draw direction icon
            if direction_icon:
                # Apply tinting if needed
                if direction_tint:
                    # Convert hex color to RGB tuple
                    rgb_color = ImageColor.getrgb(direction_tint)
                    
                    # Create a solid color image with our tint
                    tint = Image.new('RGBA', direction_icon.size, (*rgb_color, 255))
                    
                    # Apply tint by using the icon as a mask
                    mask = direction_icon.split()[3]
                    tinted_icon = Image.new('RGBA', direction_icon.size, (0, 0, 0, 0))
                    tinted_icon.paste(tint, (0, 0), mask)
                    direction_icon = tinted_icon
                
                # Paste direction icon
                img.paste(direction_icon, (int(stats_x), int(icons_y)), direction_icon)
                stats_x += rank_change_icon_size[0] + horizontal_spacing//2
            
            # Draw rank icon
            if rank_icon:
                # Paste rank icon
                img.paste(rank_icon, (int(stats_x), int(icons_y)), rank_icon)

    def _render_podium(self, img, results):
        """
        Render the podium section with medals and player information
        
        Args:
            img: The PIL image to draw on
            results: List of player results
        """
        draw = ImageDraw.Draw(img)
        
        # Get spacing configurations
        vertical_spacing = self.podium_style['vertical_spacing']
        horizontal_spacing = self.podium_style['horizontal_spacing']
        
        # Get configuration parameters for medals
        medal_width = self.podium_style['medal_width']
        medal_height = self.podium_style['medal_height']
        position_size = self.podium_style['position_size']
        position_x = self.podium_style['position_x']
        position_offset_x = self.podium_style['position_offset_x']
        position_offset_y = self.podium_style['position_offset_y']
        
        # Get the general podium start_x (for elements other than medals and Mii)
        podium_start_x = self.podium_style['start_x']

        # Initialize y position tracker - start at the configured start_y position
        y_pos = self.podium_style['start_y']
        
        # Draw medals for top positions
        for i in range(min(self.podium_count, len(results) // self.team_size)):
            # Reset x position tracker for each line
            x_pos = 0
            
            # Get position number and color
            position = str(i + 1)
            medal_color = self.colors['positions'][position]
            
            # Get size based on position
            position_size = self.podium_style['position_sizes'][i]
            name_size = self.podium_style['name_sizes'][i]
            stats_size = self.podium_style['stats_sizes'][i]
            
            # Draw medal rectangle
            draw.rectangle(
                [(x_pos, y_pos), (x_pos + medal_width, y_pos + medal_height)],
                fill=medal_color
            )
            x_pos += medal_width + horizontal_spacing
            
            # Draw position text with position-specific size
            position_font = ImageFont.truetype(self.font_file, position_size)
            position_text = f"#{position}"
            position_y = y_pos + position_offset_y
            
            # Update x_pos with position_x config value
            x_pos = position_x + position_offset_x
            
            draw.text(
                (x_pos, position_y),
                position_text,
                fill=medal_color,
                font=position_font
            )
            
            # Update x_pos after drawing position text
            position_width = draw.textlength(position_text, font=position_font)
            x_pos += position_width + horizontal_spacing
            
            # Add WINNER text for the first position
            if i == 0:
                # Get winner font size and center_x from config
                winner_font_size = self.podium_style['winner']['font_size']
                winner_font = ImageFont.truetype(self.font_file, winner_font_size)
                winner_text = "WINNER"
                
                # Use podium_start_x for winner text positioning instead of center_x
                center_x = podium_start_x  # Use the new start_x parameter
                
                # Calculate the x position to center the text
                winner_width = draw.textlength(winner_text, font=winner_font)
                winner_x = center_x - winner_width // 2
                
                # Draw the centered WINNER text
                draw.text(
                    (winner_x, position_y),
                    winner_text,
                    fill=self.colors['gold'],
                    font=winner_font
                )
                
                # After drawing the first position's row, increment y_pos
                y_pos += medal_height + vertical_spacing
                
                # Get Mii configuration from the updated config structure
                mii_config = self.podium_style['mii']
                mii_size = mii_config['size']
                mii_horizontal_spacing = mii_config['horizontal_spacing']
                mii_y_offset = mii_config['y_offset']
                team_size = self.format_config['team_size']
                
                # For larger team sizes (5v5, 6v6), draw Miis vertically
                if team_size > 4:
                    # Draw Miis vertically alongside player names using the new method
                    self._draw_miis_vertical(
                        img, 
                        results, 
                        i,  # team_index 
                        y_pos, 
                        podium_start_x
                    )
                else:
                    # Apply y_offset to the current y_pos
                    mii_y_pos = y_pos + mii_y_offset
                    
                    # Calculate total width of all Miis to center them
                    total_miis = team_size
                    total_mii_width = (mii_size * total_miis) + (mii_horizontal_spacing * (total_miis - 1))
                    mii_start_x = podium_start_x - (total_mii_width // 2)
                    
                    # Draw Mii(s) for winning player/team
                    for team_member_idx in range(team_size):
                        # Calculate team member index in results
                        player_idx = i * team_size + team_member_idx
                        if player_idx < len(results):
                            player_data = results[player_idx]
                            mii_url = player_data["mii"]
                            
                            # Calculate x position for this Mii
                            x_pos = mii_start_x + (team_member_idx * (mii_size + mii_horizontal_spacing))
                            
                            # Draw the Mii using the helper method - pass URL directly
                            self._draw_mii(img, mii_url, x_pos, mii_y_pos, mii_size)
                    
                    # Update y_pos after drawing Miis
                    mii_bottom_spacing = mii_config['bottom_spacing']
                    y_pos += mii_size + mii_bottom_spacing

            # Draw player info for each team member
            name_color = self.podium_style['name_color']
            center_x = podium_start_x  # Use the new start_x parameter
            team_y_pos = y_pos  # Start position for the team
            
            # Loop through each team member
            for team_member_idx in range(self.team_size):
                # Calculate player index in results array
                player_idx = i * self.team_size + team_member_idx
                if player_idx < len(results):
                    player_data = results[player_idx]
                    
                    # Draw this team member's info
                    member_y_pos = self._draw_player_info(
                        img,
                        player_data,
                        team_y_pos,
                        position_offset_y,
                        name_size,
                        stats_size,
                        center_x,
                        name_color,
                        horizontal_spacing
                    )
                    
                    # Update team y position for next member
                    team_y_pos = member_y_pos
            
            # Update overall y_pos to after the last team member
            y_pos = team_y_pos
            
            # Add extra spacing between podium entries
            y_pos += vertical_spacing
        
        return img

    def _render_regular_players(self, img, results):
        """
        Render the regular (non-podium) players section
        
        Args:
            img: The PIL image to draw on
            results: List of player results
        """
        # Get regular style configuration
        regular_style = self.format_config['regular_style']
        
        # Get configuration parameters
        name_size = regular_style['name_size']
        stats_size = regular_style['stats_size']
        horizontal_spacing = regular_style['horizontal_spacing']
        row_spacing = regular_style['row_spacing']
        name_color = regular_style['name_color']
        start_x = regular_style['start_x']
        start_y = regular_style['start_y']
        column_spacing = regular_style['column_spacing']
        column_y_offset = regular_style['column_y_offset']
        
        # Initialize position tracking
        current_x = start_x
        current_y = start_y
        
        # Calculate number of teams in the regular section
        podium_players = self.podium_count * self.team_size
        regular_teams = (len(results) - podium_players) // self.team_size
        if (len(results) - podium_players) % self.team_size > 0:
            regular_teams += 1
        
        # Render each team
        for i in range(regular_teams):
            # Position for this team (with column offset if needed)
            draw_y = current_y
            if current_x != start_x:
                draw_y += column_y_offset
            
            team_y_pos = draw_y
            
            # Draw each team member
            for team_member_idx in range(self.team_size):
                # Calculate player index in results array
                player_idx = podium_players + (i * self.team_size) + team_member_idx
                if player_idx < len(results):
                    player_data = results[player_idx]
                    
                    # Draw this team member's info
                    member_y_pos = self._draw_player_info(
                        img,
                        player_data,
                        team_y_pos,
                        0,
                        name_size,
                        stats_size,
                        current_x,
                        name_color,
                        horizontal_spacing
                    )
                    
                    # Update team y position for next member
                    team_y_pos = member_y_pos
            
            # Calculate total height of this team for row spacing
            team_height = team_y_pos - draw_y
            
            # Move to next position
            # Alternate between columns
            if current_x == start_x:
                # Move to second column
                current_x += column_spacing
            else:
                # Move back to first column and down a row
                current_x = start_x
                current_y += team_height + row_spacing
        
        return img

    def _draw_player_info(self, img, player_data, y_pos, position_offset_y, name_size, stats_size, center_x, name_color, horizontal_spacing):
        """
        Draw player name and score line together
        
        Args:
            img: The PIL image to draw on
            player_data: Dictionary containing player information
            y_pos: Current vertical position
            position_offset_y: Vertical offset for elements
            name_size: Font size for player name
            stats_size: Font size for stats
            center_x: Horizontal center position
            name_color: Color for the player name
            horizontal_spacing: Spacing between horizontal elements
            
        Returns:
            Updated y_pos after drawing all elements
        """
        draw = ImageDraw.Draw(img)
        player_name = player_data["name"]
        
        # Create font for player name
        name_font = ImageFont.truetype(self.font_file, name_size)
        
        # Calculate x position to center the player name
        name_width = draw.textlength(player_name, font=name_font)
        name_x = center_x - name_width // 2
        
        # Calculate vertical position for name based on y_pos
        name_y = y_pos + position_offset_y
        
        # Draw player name centered at center_x
        draw.text(
            (name_x, name_y),
            player_name,
            fill=name_color,
            font=name_font
        )
        
        # Update y_pos after drawing name
        y_pos += name_size + self.podium_style['vertical_spacing']
        
        # Calculate stats position based on current y_pos
        stats_y = y_pos + position_offset_y
        
        # Draw player stats line with all components
        self._draw_player_score_line(
            img, 
            player_data,
            center_x, 
            stats_y,
            stats_size,
            horizontal_spacing
        )
        
        # Update y_pos after drawing stats
        y_pos += stats_size + self.podium_style['vertical_spacing']
        
        return y_pos

    def _apply_shadow_to_image(self, img, shadow_color=(0, 0, 0), shadow_offset=(2, 2)):
        """
        Apply a shadow effect to the entire image by creating a copy and offsetting it
        
        Args:
            img: The PIL image to apply shadow to
            shadow_color: Color tuple for the shadow
            shadow_offset: (x, y) offset for the shadow
            
        Returns:
            New image with shadow effect
        """
        # Create a copy of the original image for the shadow
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Create a shadow image (black version of original)
        shadow = Image.new('RGBA', img.size, (0, 0, 0, 0))
        shadow.paste(shadow_color, (0, 0), img.split()[3])  # Use alpha channel as mask
        
        # Create a new image that can fit both the original and the shadow
        combined_width = img.width + abs(shadow_offset[0])
        combined_height = img.height + abs(shadow_offset[1])
        combined = Image.new('RGBA', (combined_width, combined_height), (0, 0, 0, 0))
        
        # Calculate paste positions
        shadow_pos = (max(0, shadow_offset[0]), max(0, shadow_offset[1]))
        img_pos = (max(0, -shadow_offset[0]), max(0, -shadow_offset[1]))
        
        # Paste shadow first, then the original image
        combined.paste(shadow, shadow_pos, shadow.split()[3])
        combined.paste(img, img_pos, img.split()[3])
        
        return combined

    def preload_common_assets(self):
        """Preload commonly used assets in parallel"""
        paths_to_load = []
        
        # Add direction icons
        for direction in ["up", "down", "neutral", "right"]:
            paths_to_load.append(self._get_direction_icon_path(direction))
        
        # Add rank icons for all ranks
        for rank in ["tin", "bronze", "silver", "gold", "emerald", "sapphire", 
                    "ruby", "duke", "master", "grandmaster", "monarch", "sovereign"]:
            paths_to_load.append(self._get_rank_icon_path(rank))
        
        if not paths_to_load:
            return
        
        start_time = time.time()
        
        # Update progress tracking
        self.total_steps += len(paths_to_load)
        
        # Load assets one by one
        for path in paths_to_load:
            self._load_image(path)
            self._update_progress(1, f"Preloaded: {os.path.basename(path)}")
            
        elapsed_time = time.time() - start_time

    def generate(self, results, subtitle=None):
        """
        Generate the tournament results image
        
        Args:
            results: List of player/team results to display
            subtitle: Optional subtitle text for the image
        """
        start_time = time.time()
        
        # Reset progress tracking
        self.completed_steps = 0
        
        # Simplified progress tracking with fewer steps:
        # 1. Asset preloading (including Miis)
        # 2. Image rendering (all rendering steps combined)
        # 3. Final processing and composition
        self.total_steps = 3
        
        # Add steps for Mii loading (one per player with a Mii)
        mii_count = sum(1 for player in results if player.get("mii") is not None)
        self.total_steps += mii_count
        
        # Preload common assets (rank icons, direction icons)
        self.preload_common_assets()
        self._update_progress(1, "Preloaded common assets")
        
        # Prefetch all Mii images
        mii_urls = []
        for player in results:
            if player.get("mii") is not None:
                mii_urls.append(player["mii"]) 
                
        if mii_urls:
            prefetch_start = time.time()
            for url in mii_urls:
                self._load_image(url)
                self._update_progress(1, f"Loaded Mii: {os.path.basename(url)[:30]}")
            elapsed = time.time() - prefetch_start
    
        # Update progress for starting the rendering process
        self._update_progress(0, "Rendering tournament results image...")
        
        # Create a transparent canvas for drawing content
        content_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        
        # Combine all rendering steps
        content_img = self._render_header(content_img, subtitle)
        content_img = self._render_podium(content_img, results)
        if len(results) > self.podium_count:
            content_img = self._render_regular_players(content_img, results)
        
        # Get shadow parameters
        shadow_offset = tuple(self.header_config['shadow_offset'])
        shadow_color = (0, 0, 0)  # Pure black
        
        # Apply shadow effect to the entire content
        shadowed_img = self._apply_shadow_to_image(content_img, shadow_color, shadow_offset)
        
        # Complete the rendering step
        self._update_progress(1, "Image rendered successfully")
        
        # Create background and final composition (final step)
        background = self._create_base_image()
        
        # Create final image by combining shadowed content with background
        final_img = Image.new('RGBA', background.size, (0, 0, 0, 0))
        final_img.paste(background, (0, 0))
        
        # Calculate position to center the shadowed image on background
        x_pos = (background.width - shadowed_img.width) // 2
        y_pos = (background.height - shadowed_img.height) // 2
        
        # Paste the shadowed content onto the background
        final_img.paste(shadowed_img, (x_pos, y_pos), shadowed_img)
        self._update_progress(1, "Final image composition completed")
        
        # Report total generation time
        elapsed_time = time.time() - start_time
        
        return final_img