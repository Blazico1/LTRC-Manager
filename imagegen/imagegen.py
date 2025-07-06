import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageColor

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

class TournamentImageGenerator:
    def __init__(self, format_type):
        """
        Initialize the tournament image generator with a specific format type.
        
        Args:
            format_type: The format of the tournament (e.g., "FFA", "2v2")
        """
        # Load configuration from the imagegen directory
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Store the format type
        self.format_type = format_type
        
        # Store all commonly used configuration sections as class attributes
        self.width = self.config['width']
        self.height = self.config['height']
        self.font_file = self.config['font_file']
        self.colors = self.config['colors']
        self.asset_dirs = self.config['asset_dirs']
        
        # Format specific configurations
        self.format_config = self.config['formats'][self.format_type]
        self.header_config = self.format_config['header']
        self.podium_style = self.format_config['podium_style']
        self.podium_count = self.format_config['podium_count']
        self.team_size = self.format_config['team_size']

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

    def _draw_mii(self, img, player_name, x_pos, y_pos, mii_size):
        """
        Draw a player's Mii image at the specified position
        
        Args:
            img: The PIL image to draw on
            player_name: Name of the player to load Mii for
            x_pos: X position to draw the Mii
            y_pos: Y position to draw the Mii
            mii_size: Size (width and height) of the Mii image
            
        Returns:
            None
        """
        # Load player Mii image
        mii_directory = self.asset_dirs['miis']
        mii_filename = f"{player_name}.png"
        mii_path = os.path.join(os.path.dirname(__file__), mii_directory, mii_filename)
        default_mii_path = os.path.join(os.path.dirname(__file__), mii_directory, "Default.png")
        
        try:
            # Try to load player's Mii
            mii_img = Image.open(mii_path)
            if mii_img.size != (mii_size, mii_size):
                mii_img = mii_img.resize((mii_size, mii_size))
        except (FileNotFoundError, IOError):
            try:
                # Fall back to default Mii
                mii_img = Image.open(default_mii_path)
                if mii_img.size != (mii_size, mii_size):
                    mii_img = mii_img.resize((mii_size, mii_size))
            except (FileNotFoundError, IOError):
                mii_img = None
        
        # Paste Mii image if available
        if mii_img:
            # Convert to RGBA if needed
            if mii_img.mode == 'P' and 'transparency' in mii_img.info:
                mii_img = mii_img.convert('RGBA')
            
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
            horizontal_spacing: Horizontal spacing between elements
            
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
                player_name = player_data["name"]
                
                # Calculate vertical position for this Mii
                member_y = mii_y_pos + (member_idx * (mii_size + mii_vertical_spacing))
                
                # Draw the Mii
                self._draw_mii(img, player_name, mii_x, member_y, mii_size)

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
        new_mmr_text = f"{new_mmr}"
        
        # Calculate MMR color
        mmr_color = self.colors['mmr_up'] if mmr_change >= 0 else self.colors['mmr_down']
        
        # Load icons for width calculation
        rank_directory = self.asset_dirs['ranks']
        
        # Load direction icon
        if rank_change > 0:
            direction_file = "up.png"
            direction_tint = self.colors['mmr_up']
        elif rank_change < 0:
            direction_file = "down.png"
            direction_tint = self.colors['mmr_down']
        else:
            direction_file = "neutral.png"
            direction_tint = None
            
        direction_icon_path = os.path.join(os.path.dirname(__file__), rank_directory, direction_file)
        try:
            direction_icon = Image.open(direction_icon_path)
        except (FileNotFoundError, IOError):
            direction_icon = None
        
        # Load rank icon
        rank_icon_path = os.path.join(os.path.dirname(__file__), rank_directory, f"{rank}.png")
        try:
            rank_icon = Image.open(rank_icon_path)
        except (FileNotFoundError, IOError):
            rank_icon = None
        
        # Calculate icon sizes
        rank_change_icon_size = (stats_size - 5, stats_size - 5)
        rank_icon_size = (stats_size, stats_size)
        
        # Build stats text to calculate width for centering
        full_stats_text = f"{score_text}{separator}{mmr_text}{separator}{new_mmr_text}"
        full_stats_width = draw.textlength(full_stats_text, font=stats_font)
        
        # Add icon widths and separator to total width
        separator_width = draw.textlength(separator, font=stats_font)
        icons_width = 0
        if direction_icon:
            icons_width += rank_change_icon_size[0] + horizontal_spacing//2
        if rank_icon:
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
        
        # Draw new MMR
        draw.text((stats_x, stats_y), new_mmr_text, fill=name_color, font=stats_font)
        stats_x += draw.textlength(new_mmr_text, font=stats_font)
        
        # Draw separator before icons
        draw.text((stats_x, stats_y), separator, fill=name_color, font=stats_font)
        stats_x += draw.textlength(separator, font=stats_font)
        
        # Get icon vertical alignment adjustment from config and scale it with the stats size
        base_icon_y_offset = self.podium_style['icon_y_offset']
        # Scale offset based on the ratio of current size to a reference size (e.g., 40)
        reference_size = 40  # Reference font size for scaling
        icon_y_offset = base_icon_y_offset * (stats_size / reference_size)
        
        # Calculate common vertical position for both icons with configurable and scaled offset
        icons_y = stats_y + (stats_size - rank_change_icon_size[1]) // 2 + int(icon_y_offset)
        
        # Draw direction icon
        # Resize if needed
        if direction_icon.size != rank_change_icon_size:
            direction_icon = direction_icon.resize(rank_change_icon_size)
        
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
        
        # Ensure icon is in RGBA mode
        if direction_icon.mode != 'RGBA':
            direction_icon = direction_icon.convert('RGBA')
        
        # Paste direction icon
        img.paste(direction_icon, (int(stats_x), int(icons_y)), direction_icon)
        stats_x += rank_change_icon_size[0] + horizontal_spacing//2
        
        # Draw rank icon
        # Resize if needed
        if rank_icon.size != rank_icon_size:
            rank_icon = rank_icon.resize(rank_icon_size)
        
        # Ensure icon is in RGBA mode
        if rank_icon.mode != 'RGBA':
            rank_icon = rank_icon.convert('RGBA')
        
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
                            player_name = player_data["name"]
                            
                            # Calculate x position for this Mii
                            x_pos = mii_start_x + (team_member_idx * (mii_size + mii_horizontal_spacing))
                            
                            # Draw the Mii using the helper method
                            self._draw_mii(img, player_name, x_pos, mii_y_pos, mii_size)
                    
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

    def generate(self, results, subtitle=None):
        """
        Generate the tournament results image
        
        Args:
            results: List of player/team results to display
            subtitle: Optional subtitle text for the image
        """
        # Create a transparent canvas for drawing content
        content_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        
        # Add header (title and subtitle)
        content_img = self._render_header(content_img, subtitle)
        
        # Render podium section
        content_img = self._render_podium(content_img, results)
        
        # Render regular players if there are more than podium count
        if len(results) > self.podium_count:
            content_img = self._render_regular_players(content_img, results)
        
        # Get shadow parameters
        shadow_offset = tuple(self.header_config['shadow_offset'])
        shadow_color = (0, 0, 0)  # Pure black
        
        # Apply shadow effect to the entire content
        shadowed_img = self._apply_shadow_to_image(content_img, shadow_color, shadow_offset)
        
        # Create background
        background = self._create_base_image()
        
        # Create final image by combining shadowed content with background
        final_img = Image.new('RGBA', background.size, (0, 0, 0, 0))
        final_img.paste(background, (0, 0))
        
        # Calculate position to center the shadowed image on background
        x_pos = (background.width - shadowed_img.width) // 2
        y_pos = (background.height - shadowed_img.height) // 2
        
        # Paste the shadowed content onto the background
        final_img.paste(shadowed_img, (x_pos, y_pos), shadowed_img)
        
        return final_img

if __name__ == "__main__":
    # Example usage
    generator = TournamentImageGenerator("6v6")
    results = [
    {"name": "Blazico", "score": 185, "mmr_change": +32, "new_mmr": 2185},
    {"name": "Ryumi", "score": 172, "mmr_change": -28, "new_mmr": 2072},
    {"name": "KogMawMain", "score": 168, "mmr_change": +25, "new_mmr": 1968},
    {"name": "Gaberboo", "score": 155, "mmr_change": +22, "new_mmr": 1855},
    {"name": "TealS", "score": 142, "mmr_change": +18, "new_mmr": 1742},
    {"name": "Fern", "score": 135, "mmr_change": +15, "new_mmr": 1635},
    {"name": "Police", "score": 128, "mmr_change": +12, "new_mmr": 1528},
    {"name": "Turtspotato", "score": 118, "mmr_change": +8, "new_mmr": 1418},
    {"name": "Rockyroller", "score": 105, "mmr_change": +5, "new_mmr": 1305},
    {"name": "Bepisman", "score": 95, "mmr_change": +3, "new_mmr": 1195},
    {"name": "Rowan Atkinson", "score": 85, "mmr_change": +1, "new_mmr": 1085},
    {"name": "King William III", "score": 75, "mmr_change": 0, "new_mmr": 1000}
]
    subtitle = "Event A 12-12-1234"
    img = generator.generate(results, subtitle)
    # img.show()  # Display the image
    img.save("tournament_results.png")  # Save to file