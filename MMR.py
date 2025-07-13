import gspread
from gspread.utils import ValueRenderOption
import numpy as np
from google.oauth2.service_account import Credentials
import sys
import os
import json

'''
author: Zakaria Hayaty (Blazico)
'''

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

# Define the MMR thresholds and their corresponding values
MMR_THRESHOLDS = {
    10: 500, 20: 1000, 30: 1500, 
    40: 2000, 50: 2250, 60: 2500, 
    70: 3000, 80: 3250, 90: 3500, 
    100: 4000, 110: 4250, 120: 4500, 
    130: 5250, 140: 5500, 
    150: 6250, 160: 6500, 
    170: 7250, 180: 7500
}

class LTRC_manager():
    def __init__(self) -> None:
        # Load configuration
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        config_path = os.path.join(base_path, "config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Get sheetname from config
        self.sheetname = config.get('sheetname', 'LTRC Manager MMR calculator')

        # Define the scope
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file','https://www.googleapis.com/auth/drive']

        # Add your service account file
        credentials_path = os.path.join(base_path, 'auto-mmr-calculator-9676e1429d9a.json')
        creds = Credentials.from_service_account_file(credentials_path, scopes=scope)

        # Authorize the clientsheet
        client = gspread.authorize(creds)

        # Get the instance of the Spreadsheet
        sheet = client.open(self.sheetname) 

        # Get the individual sheets of the Spreadsheet
        # self.Team_Rankings_and_Personal_Evaluation = sheet.get_worksheet(0)
        # self.Rules_and_Ranks = sheet.get_worksheet(1)
        self.TR_Tables = sheet.get_worksheet(2)
        self.Table_stuff = sheet.get_worksheet(3)
        self.Playerdata = sheet.get_worksheet(4)
        # self.Teamdata = sheet.get_worksheet(5)
        self.Placements = sheet.get_worksheet(6)

        # Get the mode from the spreadsheet
        self.mode = self.Table_stuff.get("C1")[0][0] 
            
        # Toggle flag for 32 track mode
        self.flag_32track = False
        # Toggle flag for 200cc mode
        self.flag_200cc = False

    def _update_progress(self, value, message=None):
        """Update the progress callback if provided"""
        if hasattr(self, 'progress_callback') and self.progress_callback and callable(self.progress_callback):
            self.progress_callback(value, message)

    def LTRC_routine(self, progress_callback=None):
        """
        Main routine to process data with optional progress tracking
        
        Args:
            progress_callback: Optional function to report loading progress
        """
        # Store the progress callback for use by other methods
        self.progress_callback = progress_callback
        
        # Update progress: Starting
        self._update_progress(0, "Initialising tournament data processing...")
        
        # Get data from the sheet
        self.get_all()
        self._update_progress(40, "Analysing player rankings and calculating team positions...")
        
        # Process rankings
        self.find_ranking()
        self._update_progress(60, "Determining K-values based on player positions...")
        
        # Find K-values
        self.find_k_values()
        self._update_progress(80, "Calculating MMR changes and final ratings...")
        
        # Calculate new MMR values
        self.calc_new_MMR()
        self._update_progress(100, "Tournament data processing completed successfully!")
        
        # Clean up
        self.progress_callback = None

    def get_all(self):
        '''
        This method reads all the required data from the spreadsheet using a single API call
        '''
        # Define range based on the mode
        match self.mode:
            case "FFA":
                range_str = "B3:E14"
            case "2vs2":
                range_str = "B23:E39"
            case "3vs3":
                range_str = "B48:E62"
            case "4vs4":
                range_str = "B71:E84"
            case "5vs5":
                range_str = "B92:E104"
            case "6vs6":
                range_str = "B92:E104"

        self._update_progress(5, f"Retrieving {self.mode} tournament data from Google Sheets...")
        
        # Get all data in a single API call
        data = self.TR_Tables.get(range_str)
        self._update_progress(15, "Extracting player names, scores and current MMR values...")
        
        # Process the data
        self.racers = []
        self.scores = []
        self.MMRs = []
        
        for row in data:
            # Only process rows with data
            if row and len(row) >= 2 and row[0] != '':
                self.racers.append(row[0])
                # Convert scores to integers
                self.scores.append(int(row[1]))
                # Get MMR from column E (index 3)
                if len(row) > 3:
                    self.MMRs.append(row[3])
                else:
                    self.MMRs.append("???")

        if len(self.racers) == 0:
            raise ValueError("No racers found in the sheet")
        
        if len(self.racers) != len(self.scores) or len(self.racers) != len(self.MMRs):
            raise ValueError("The number of racers, scores and MMRs do not match")
        
        # Add any new players to the sheets
        self._update_progress(20, "Checking for new players and adding them to database...")
        self.handle_new_players()
        
        # Calculate placements for unplaced players
        self._update_progress(25, "Calculating placement progress for unplaced players...")
        self.calculate_placement()

        # Calculate the average MMR of the room
        self._update_progress(35, "Calculating room MMR average for balanced matchmaking...")
        self.average_room_MMR = np.average(self.LR_list)

    def handle_new_players(self):
        '''
        This method checks for new players and adds them to both Playerdata and Placements tabs
        '''
        new_players = []
        
        # Check each racer to see if they exist in the Playerdata sheet
        for racer in self.racers:
            cell = self.Playerdata.find(racer)
            if cell is None:
                # If the racer is not found, add them to the new_players list
                new_players.append(racer)
        
        # If there are new players, add them to both sheets
        if new_players:
            # Get all player names from Playerdata and Placements
            playerdata_names = self.Playerdata.col_values(1)
            placements_names = self.Placements.col_values(1)
            
            playerdata_row = len(playerdata_names) + 1  # First empty row
            placements_row = len(placements_names) + 1  # First empty row
            
            # If Placements has header rows, adjust the start index
            if placements_row < 5:
                placements_row = 5  # Start after header rows
            
            for player in new_players:
                # Add player to Playerdata
                self.Playerdata.update_cell(playerdata_row, 1, player)  # Name
                self.Playerdata.update_cell(playerdata_row, 4, "???")   # MMR
                playerdata_row += 1
                
                # Add player to Placements
                self.Placements.update_cell(placements_row, 1, player)  # Name
                self.Placements.update_cell(placements_row, 2, "")      # Completion
                self.Placements.update_cell(placements_row, 8, "0")     # MMR Accumulation
                placements_row += 1
            
            print(f"Added {len(new_players)} new player(s) to the sheets: {', '.join(new_players)}")

    def calculate_placement(self):
        '''
        This method assumes the MMR of unplaced racers and calculates their placements
        Using a single API call to read the complete Placements worksheet
        '''
        num = len(self.racers)
        MMRs = self.MMRs
        self.LR_list = []
        self.is_placed = []
        self.placement_updates = []
        self.completion = []

        # Get all placement data at once in a single API call
        placements_data = self.Placements.get_all_values()[4:]  # Skip header rows
        
        # Create a dictionary for quick lookups
        placements_dict = {}
        for row_idx, row in enumerate(placements_data, start=5):
            if row and len(row) > 0 and row[0]:
                placements_dict[row[0]] = {
                    'row': row_idx,
                    'completion': row[1] if len(row) > 1 else None,
                    'point1': row[3] if len(row) > 3 and row[3] else None,
                    'point2': row[4] if len(row) > 4 and row[4] else None,
                    'point3': row[5] if len(row) > 5 and row[5] else None,
                    'mmr_accum': row[7] if len(row) > 7 and row[7] else "0"
                }
        self.placements_dict = placements_dict

        # Find the first empty row
        empty_row = 5
        while empty_row < len(placements_data) + 5 and placements_data[empty_row - 5] and placements_data[empty_row - 5][0]:
            empty_row += 1
        
        # Cache for playerdata lookups
        playerdata_rows = {}
        
        for i in range(num):
            # If the MMR is unknown
            if MMRs[i] == "???" or MMRs[i] == "":
                self.is_placed.append(False)
                # Get the name of the racer and their score
                racer = self.racers[i]
                points = [self.scores[i]]
                if self.flag_32track:
                    points[0] /= 2.67

                # Check if player exists in placements
                if racer in placements_dict:
                    # Player exists in placements
                    row = placements_dict[racer]['row']
                    completion = placements_dict[racer]['completion']
                    
                    if not completion:
                        self.completion.append("1/3")
                        self.placement_updates.append((row, 2, "1/3"))
                        self.placement_updates.append((row, 4, points[0]))
                        
                    elif completion == "1/3":
                        self.completion.append("2/3")
                        self.placement_updates.append((row, 2, "2/3"))
                        self.placement_updates.append((row, 5, points[0]))

                        # Get the points of the previous event
                        if placements_dict[racer]['point1']:
                            points.append(float(placements_dict[racer]['point1']))
                    
                    elif completion == "2/3":
                        self.completion.append("3/3")
                        # This event places the racer
                        self.is_placed[i] = True

                        self.placement_updates.append((row, 2, "3/3"))
                        self.placement_updates.append((row, 6, points[0]))

                        # Get the points of the previous events
                        if placements_dict[racer]['point1']:
                            points.append(float(placements_dict[racer]['point1']))
                        if placements_dict[racer]['point2']:
                            points.append(float(placements_dict[racer]['point2']))
                    else:
                        # Placements and playerdata mismatch, throw error
                        raise ValueError(f"Placement and playerdata for {racer} is inconsistent: {completion} completion but MMR is unknown")
                else:
                    # Player doesn't exist in placements, add them
                    row = empty_row
                    empty_row += 1  # Increment for next new player
                    
                    self.completion.append("1/3")
                    self.placement_updates.append((row, 1, racer))
                    self.placement_updates.append((row, 2, "1/3"))
                    self.placement_updates.append((row, 4, points[0]))

                # Calculate the average number of points in the past event(s)
                average = np.average(points)

                # Calculate the MMR of the racer based on the average
                for threshold, mmr in MMR_THRESHOLDS.items():
                    if average < threshold:
                        MMR = mmr
                        break
                else:
                    MMR = 7750

                if racer in placements_dict and placements_dict[racer]['completion'] == "2/3":
                    # MMR is average with previous season MMR
                    # Get the previous season MMR - use cache if available
                    if racer in playerdata_rows:
                        row_playerdata = playerdata_rows[racer]
                    else:
                        row_playerdata = self.Playerdata.find(racer).row
                        playerdata_rows[racer] = row_playerdata
                    
                    previous_season_MMR = self.Playerdata.cell(row_playerdata, 11).value

                    if previous_season_MMR is not None and previous_season_MMR != "???":
                        previous_season_MMR = int(previous_season_MMR)
                        MMR = (MMR + previous_season_MMR) / 2

                # Add previously gained MMR to the new MMR
                if racer in placements_dict and placements_dict[racer]['mmr_accum']:
                    MMR += int(placements_dict[racer]['mmr_accum'])
                
                self.LR_list.append(MMR)
            else:
                self.is_placed.append(True)
                self.completion.append("")
                self.LR_list.append(int(MMRs[i]))

    def find_ranking(self):
        '''
        This method finds the rankings of the racers, taking ties into account
        '''
        
        rankings = [1] # list holding the rankings of the racers

        # get team scores depending on the mode
        match self.mode:
            case "FFA":
                scores = self.scores
            case "2vs2":
                scores = [sum(self.scores[i:i+2]) for i in range(0, len(self.scores), 2)]
            case "3vs3":
                scores = [sum(self.scores[i:i+3]) for i in range(0, len(self.scores), 3)]
            case "4vs4":
                scores = [sum(self.scores[i:i+4]) for i in range(0, len(self.scores), 4)]
            case "5vs5":
                scores = [sum(self.scores[i:i+5]) for i in range(0, len(self.scores), 5)]
            case "6vs6":
                scores = [sum(self.scores[i:i+6]) for i in range(0, len(self.scores), 6)]

        # Find the rankings of the racers/teams
        for i in range(1,len(scores)):
            if scores[i] == scores[i-1]:
                rankings.append(rankings[i-1])
            else:
                rankings.append(i+1)

        # Make the list the right size again
        match self.mode:
            case "FFA":
                rankings = rankings
            case "2vs2":
                rankings = [rankings[i//2] for i in range(len(rankings)*2)]
            case "3vs3":
                rankings = [rankings[i//3] for i in range(len(rankings)*3)]
            case "4vs4":
                rankings = [rankings[i//4] for i in range(len(rankings)*4)]
            case "5vs5":
                rankings = [rankings[i//5] for i in range(len(rankings)*5)]
            case "6vs6":
                rankings = [rankings[i//6] for i in range(len(rankings)*6)]
        
        self.rankings = rankings   # Save the rankings of the race to the class     

    def find_k_values(self):
        '''
        This method makes a list of k values corresponding to the rankings of the racers and the mode
        '''
        # Insert the correct number of players into the sheet
        num_players = len(self.racers)
        self.Table_stuff.update("C1", [[self.mode]])
        self.Table_stuff.update("C2", [[num_players]])

        # Get the right k values depending on the mode
        match self.mode:
            case "FFA":
                range_str = "E11:E22"
            case "2vs2":
                range_str = "F11:F16"
            case "3vs3":
                range_str = "G11:G14"
            case "4vs4":
                range_str = "H11:H13"
            case "5vs5":
                range_str = "I11:I12"
            case "6vs6":
                range_str = "I11:I12"
                
        k_list = self.Table_stuff.get(range_str)
        
        # Process k values
        # Flatten the list and convert strings to integers
        k_list = [int(value) for sublist in k_list for value in sublist]

        # k values corresponding to the rankings
        k_values = []
        for i in range(len(self.rankings)):
            k_values.append(k_list[self.rankings[i]-1])     # -1 because the rankings start at 1 but the list starts at 0      

        self.k_values = k_values  # Save the k values to the class
        
    def calc_new_MMR(self):
        C = int(self.Table_stuff.get("E1")[0][0]) # Get the C value from the spreadsheet
        LR = self.LR_list
        K = self.k_values
        u = self.average_room_MMR
        p_mu = 5800

        # list holding the change in MMR for each player
        delta_MMRs = []

        for i in range(len(LR)):
            # The equation for the change in MMR
            delta_MMRs.append(C/12 +  C/(1+11**(-(u-LR[i])/p_mu)) - K[i])

        # Average MMR gain for the teams
        match self.mode:
            case "FFA":
                self.delta_MMRs = delta_MMRs
            case "2vs2":
                delta_MMRs = [sum(delta_MMRs[i:i+2])/2 for i in range(0, len(delta_MMRs), 2)]
                self.delta_MMRs = [delta_MMRs[i//2] for i in range(len(delta_MMRs)*2)]
            case "3vs3":
                delta_MMRs = [sum(delta_MMRs[i:i+3])/3 for i in range(0, len(delta_MMRs), 3)]
                self.delta_MMRs = [delta_MMRs[i//3] for i in range(len(delta_MMRs)*3)]
            case "4vs4":
                delta_MMRs = [sum(delta_MMRs[i:i+4])/4 for i in range(0, len(delta_MMRs), 4)]
                self.delta_MMRs = [delta_MMRs[i//4] for i in range(len(delta_MMRs)*4)]
            case "5vs5":
                delta_MMRs = [sum(delta_MMRs[i:i+5])/5 for i in range(0, len(delta_MMRs), 5)]
                self.delta_MMRs = [delta_MMRs[i//5] for i in range(len(delta_MMRs)*5)]
            case "6vs6":
                delta_MMRs = [sum(delta_MMRs[i:i+6])/6 for i in range(0, len(delta_MMRs), 6)]
                self.delta_MMRs = [delta_MMRs[i//6] for i in range(len(delta_MMRs)*6)]
    
        # Modify MMR if 32 track mode is enabled
        if self.flag_32track:
            self.delta_MMRs = [delta_MMR * 2.67 if delta_MMR > 0 else delta_MMR * 0.67 for delta_MMR in self.delta_MMRs]
        
        # Modify MMR if 200cc mode is enabled - halve losses only
        if self.flag_200cc:
            self.delta_MMRs = [delta_MMR if delta_MMR > 0 else delta_MMR * 0.5 for delta_MMR in self.delta_MMRs]
        
        # Round the MMR changes to the nearest integer
        self.delta_MMRs = [int(round(delta_MMR)) for delta_MMR in self.delta_MMRs]

        # Add the change in MMR to the old MMR
        self.MMR_new = np.add(self.LR_list, self.delta_MMRs)
        
        # Round the new MMR values to integers
        self.MMR_new = [int(round(mmr)) for mmr in self.MMR_new]

    def fill_MMR_change_table(self):
        '''
        This method fills the MMR change table in the spreadsheet
        '''
        match self.mode:
            case "FFA":
                x = 1
            case "2vs2":
                x = 2
            case "3vs3":
                x = 3
            case "4vs4":
                x = 4
            case "5vs5":
                x = 5
            case "6vs6":
                x = 6

        data = self.delta_MMRs
        deltas = []
        for i, value in enumerate(data):
            deltas.append(value)
            if (i + 1) % x == 0:
                deltas.append("")
                if x == 5:
                    deltas.append("")

        match self.mode:
            case "FFA":
                self.TR_Tables.update("F3:F14", [[delta] for delta in self.delta_MMRs])
            case "2vs2":
                self.TR_Tables.update("F23:F40", [[delta] for delta in deltas])
            case "3vs3":
                self.TR_Tables.update("F48:F63", [[delta] for delta in deltas])
            case "4vs4":
                self.TR_Tables.update("F71:F85", [[delta] for delta in deltas])
            case "5vs5":
                self.TR_Tables.update("F92:F105", [[delta] for delta in deltas])
            case "6vs6":
                self.TR_Tables.update("F92:F105", [[delta] for delta in deltas])

    def fill_rank_change_table(self):
        '''
        This method fills the rank change table in the spreadsheet
        '''
        # Dictionary holding the rank ranges
        rankings_dict = {0: "Tin", 1: "Tin", 2: "Bronze", 3: "Silver", 
                         4: "Gold", 5: "Emerald", 6: "Sapphire", 
                         7: "Ruby", 8: "Duke", 9: "Master", 
                         10: "Grandmaster", 11: "Monarch", 12: "Monarch",
                         13: "Monarch", 14: "Monarch", 15: "Sovereign"}
        
        # Get the old MMRs and the new MMRs
        old_ranks = [int(item)//1000 if item != "???" else -1 for item in self.MMRs]
        new_ranks = [int(item)//1000 for item in self.MMR_new]

        # Take the difference between the old and new ranks
        differences = np.subtract(new_ranks, old_ranks)

        # List holding the rank changes as strings
        rank_changes = []
        up_down = []

        for i, difference in enumerate(differences):
            if not self.is_placed[i]:
                # Racer is unplaced
                rank_changes.append(self.completion[i])
                up_down.append("-")

            elif difference == 0:
                # No change in rank
                rank_changes.append("")
                up_down.append("-")
            else:
                if old_ranks[i] == -1:
                    # Racer had no previous rank
                    rank_changes.append(rankings_dict[new_ranks[i]])
                    up_down.append("▲")
                elif rankings_dict[old_ranks[i]] == rankings_dict[new_ranks[i]]:
                    # No change in rank
                    rank_changes.append("")
                    up_down.append("-")
                else:
                    # Change in rank
                    rank_changes.append(rankings_dict[new_ranks[i]])
                    if difference > 0:
                        up_down.append("▲")
                    else:
                        up_down.append("▼")

        # Fill the rank change table
        match self.mode:
            case "FFA":
                x = 1
            case "2vs2":
                x = 2
            case "3vs3":
                x = 3
            case "4vs4":
                x = 4
            case "5vs5":
                x = 5
            case "6vs6":
                x = 6

        rank_changes_list = []
        up_down_list = []

        # Add blank spaces to the list
        for i, value in enumerate(rank_changes):
            rank_changes_list.append(value)
            up_down_list.append(up_down[i])

            if (i + 1) % x == 0:
                rank_changes_list.append("")
                up_down_list.append("")
                if x == 5:
                    rank_changes_list.append("")
                    up_down_list.append("")

        match self.mode:
            case "FFA":
                self.TR_Tables.update("I3:I14", [[rank_change] for rank_change in rank_changes])
                self.TR_Tables.update("H3:H14", [[up_down] for up_down in up_down])
            case "2vs2":
                self.TR_Tables.update("I23:I40", [[rank_change] for rank_change in rank_changes_list])
                self.TR_Tables.update("H23:H40", [[up_down] for up_down in up_down_list])
            case "3vs3":
                self.TR_Tables.update("I48:I63", [[rank_change] for rank_change in rank_changes_list])
                self.TR_Tables.update("H48:H63", [[up_down] for up_down in up_down_list])
            case "4vs4":
                self.TR_Tables.update("I71:I85", [[rank_change] for rank_change in rank_changes_list])
                self.TR_Tables.update("H71:H85", [[up_down] for up_down in up_down_list])
            case "5vs5":
                self.TR_Tables.update("I92:I105", [[rank_change] for rank_change in rank_changes_list])
                self.TR_Tables.update("H92:H105", [[up_down] for up_down in up_down_list])
            case "6vs6":
                self.TR_Tables.update("I92:I105", [[rank_change] for rank_change in rank_changes_list])
                self.TR_Tables.update("H92:H105", [[up_down] for up_down in up_down_list])

    def update_sheet(self, progress_callback=None):
        '''
        This method updates the MMRs of the players on the sheet
        
        Args:
            progress_callback: Function to report progress (percentage, message)
        '''
        # First update placement data
        placement_count = len(self.placement_updates)
        
        # Batch update placements data to reduce API calls
        if self.placement_updates:
            cell_list = []
            for idx, (row, column, value) in enumerate(self.placement_updates):
                cell_list.append(gspread.cell.Cell(row, column, value))
                
        # Execute the batch update
        self.Placements.update_cells(cell_list)
        
        # Count how many placed players we need to update
        placed_players = [i for i, is_placed in enumerate(self.is_placed) if is_placed]
        placed_count = len(placed_players)
        
        # Process placed players
        placed_processed = 0
        
        for i in placed_players:
            # Get the row of the racer
            row = self.Playerdata.find(self.racers[i]).row
            
            # Update the MMR of the racer
            self.Playerdata.update_cell(row, 4, int(self.MMR_new[i]))
            
            # Update progress
            placed_processed += 1
            if progress_callback:
                progress = 35 + int(55 * placed_processed / placed_count) if placed_count > 0 else 90
                progress_callback(progress, f"Updating Playerdata sheet: {placed_processed}/{placed_count} players - {self.racers[i]}")

    def update_placements_MMR(self, progress_callback=None):
        '''
        This method updates the MMR of the racers in the placements sheet
        
        Args:
            progress_callback: Function to report progress (percentage, message)
        '''
        # Count how many unplaced players we have
        unplaced_count = sum(1 for is_placed in self.is_placed if not is_placed)
        
        # Prepare batch update list
        cell_updates = []
        
        unplaced_processed = 0
        
        for i, completion in enumerate(self.completion):
            if completion:
                racer = self.racers[i]
                
                # Use the cached dictionary to get the row and old MMR
                row = self.placements_dict[racer]['row']
                old_mmr = int(self.placements_dict[racer]['mmr_accum']) if self.placements_dict[racer]['mmr_accum'] else 0
                
                # Calculate the new accumulated MMR
                new_mmr = old_mmr + int(self.delta_MMRs[i])
                
                # Add to batch update
                cell_updates.append(gspread.cell.Cell(row, 8, new_mmr))
                
                # Update progress
                unplaced_processed += 1
                if progress_callback:
                    progress = int(25 * unplaced_processed / unplaced_count) if unplaced_count > 0 else 25
                    progress_callback(progress, f"Updating Placements sheet: {unplaced_processed}/{unplaced_count} players - {racer}")
        
        # Execute the batch update if there are any updates to make
        if cell_updates:
            self.Placements.update_cells(cell_updates)

    def clear_table(self, progress_callback=None):
        '''
        This method clears the TR tables using batch_clear to reduce API calls
        
        Args:
            progress_callback: Function to report progress (percentage, message)
        '''
        if progress_callback:
            progress_callback(90, "Clearing tournament tables...")
            
        # Define ranges to clear based on the mode
        ranges = []
        
        match self.mode:
            case "FFA":
                ranges = ["B3:B14", "C3:C14", "F3:F14", "I3:I14"]
                self.TR_Tables.update("H3:H14", [["-"] for _ in range(12)])
            case "2vs2":
                ranges = ["B23:B39", "C23:C39", "F23:F39", "I23:I39"]
                self.TR_Tables.update("H23:H39", [["-"] for _ in range(17)])
            case "3vs3":
                ranges = ["B48:B62", "C48:C62", "F48:F62", "I48:I62"]
                self.TR_Tables.update("H48:H62", [["-"] for _ in range(15)])
            case "4vs4":
                ranges = ["B71:B84", "C71:C84", "F71:F84", "I71:I84"]
                self.TR_Tables.update("H71:H84", [["-"] for _ in range(14)])
            case "5vs5":
                ranges = ["B92:B104", "C92:C104", "F92:F104", "I92:I104"]
                self.TR_Tables.update("H92:H104", [["-"] for _ in range(13)])
            case "6vs6":
                ranges = ["B92:B104", "C92:C104", "F92:F104", "I92:I104"]
                self.TR_Tables.update("H92:H104", [["-"] for _ in range(13)])
        
        # Use batch_clear to clear all ranges in a single API call
        if ranges:
            self.TR_Tables.batch_clear(ranges)
        
        # Final progress update
        if progress_callback:
            progress_callback(100, "Sheet update complete!")

    def get_mii(self, player):
        """
        Get the Mii image URL for a player
        
        Args:
            player: Player name to look up
            
        Returns:
            str: URL to the player's Mii image or default Mii if not found
        """
        # Find the player in the sheet and get their Mii
        cell = self.Playerdata.find(player)
        if cell and (mii := self.Playerdata.cell(cell.row, 5, value_render_option=ValueRenderOption.formula).value):
            formula = mii
        else:
            # Use default Mii if player not found or no Mii set
            formula = self.Playerdata.acell("V29", value_render_option=ValueRenderOption.formula).value
            
        # Extract URL from formula
        if formula and 'IMAGE' in formula:
            start = formula.find('"')
            end = formula.rfind('"')
            if start != -1 and end != -1 and start < end:
                return formula[start+1:end]
        else:
            # Throw an error if the formula is not valid
            raise ValueError(f"Invalid Mii formula for player {player}: {formula}")

    def get_results(self):
        """
        Gathers all the relevant data and returns a list of dictionaries with player information.
        Each dictionary contains: name, score, mmr_change, new_mmr, mii, completion
        Only fetches Mii images for the winning team to reduce API calls.
        """
        # Make sure all the necessary calculations have been performed
        if not hasattr(self, 'racers') or not hasattr(self, 'scores') or not hasattr(self, 'delta_MMRs') or not hasattr(self, 'MMR_new'):
            raise ValueError("Data not fully initialized.")
            
        results = []
        
        # Determine team size based on the mode
        
        if self.mode == "FFA":
            team_size = 1
        elif self.mode == "2vs2":
            team_size = 2
        elif self.mode == "3vs3":
            team_size = 3
        elif self.mode == "4vs4":
            team_size = 4
        elif self.mode == "5vs5":
            team_size = 5
        elif self.mode == "6vs6":
            team_size = 6
            
        # Calculate the number of Miis to fetch (just for the winning team)
        miis_to_fetch = team_size
        
        # Get all Mii URLs in a batch for the winning team
        mii_urls = {}
        if miis_to_fetch > 0:
            # Get player names from the winning team
            winning_team = self.racers[:miis_to_fetch]
            
            # First, try to find the row numbers for these players
            rows = {}
            for player in winning_team:
                try:
                    cell = self.Playerdata.find(player)
                    if cell:
                        rows[player] = cell.row
                except:
                    pass
                
            # If we found any players, get their Mii formulas in a batch
            if rows:
                # Prepare batch request for formulas (col 5 is the Mii column)
                cell_ranges = []
                for player, row in rows.items():
                    cell_ranges.append(f"{chr(64+5)}{row}")  # Column E = 5
                
                # Add the default Mii cell to the batch request
                default_mii_cell = "V29"
                cell_ranges.append(default_mii_cell)
                
                # Execute batch request for formulas
                batch_formulas = self.Playerdata.batch_get(
                    cell_ranges, 
                    value_render_option=ValueRenderOption.formula
                )
                
                # Process the results
                default_mii_formula = None
                if batch_formulas and batch_formulas[-1] and batch_formulas[-1][0]:
                    default_mii_formula = batch_formulas[-1][0][0]
                    
                # Extract Mii URLs from formulas
                for i, player in enumerate(rows.keys()):
                    if (i < len(batch_formulas) and 
                        batch_formulas[i] and 
                        len(batch_formulas[i]) > 0 and 
                        len(batch_formulas[i][0]) > 0):
                        formula = batch_formulas[i][0][0]
                        if formula and 'IMAGE' in formula:
                            start = formula.find('"')
                            end = formula.rfind('"')
                            if start != -1 and end != -1 and start < end:
                                mii_urls[player] = formula[start+1:end]
                
                # Extract default Mii URL
                default_mii_url = None
                if default_mii_formula and 'IMAGE' in default_mii_formula:
                    start = default_mii_formula.find('"')
                    end = default_mii_formula.rfind('"')
                    if start != -1 and end != -1 and start < end:
                        default_mii_url = default_mii_formula[start+1:end]
    
        # Create result dictionaries for each player
        for i, name in enumerate(self.racers):
            # Get the score
            score = self.scores[i]
            
            # Get the MMR change
            mmr_change = self.delta_MMRs[i]
            
            # Get the new MMR
            new_mmr = int(self.MMR_new[i])
            
            # Get placement completion status
            completion = self.completion[i]
            
            # Get Mii URL for winning team members (or None for others)
            mii_url = None
            if i < miis_to_fetch:
                # Try to get from our batch-loaded URLs
                if name in mii_urls:
                    mii_url = mii_urls[name]
                else:
                    # Fall back to default Mii
                    mii_url = default_mii_url
        
            # Create the player dictionary with all information
            player = {
                "name": name,
                "score": score,
                "mmr_change": mmr_change,
                "new_mmr": new_mmr,
                "mii": mii_url,
                "completion": completion
            }
            
            results.append(player)
    
        return results
    
if __name__ == "__main__":
    # Create an instance of the LTRC manager
    LTRC = LTRC_manager()
    
    try:
        # Run the main processing routine without progress tracking
        LTRC.LTRC_routine()
        
        # Fill the tables with calculated data
        LTRC.fill_MMR_change_table()
        LTRC.fill_rank_change_table()
        
        # Update the player data in the sheets
        LTRC.update_sheet()
        LTRC.update_placements_MMR()
        
        # Retrieve and display results
        results = LTRC.get_results()
        
        print("\nProcessing complete. Results summary:")
        for i, player in enumerate(results[:3]):  # Show top 3 players
            print(f"{i+1}. {player['name']}: {player['score']} points, MMR change: {player['mmr_change']}")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")