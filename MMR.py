import gspread
import numpy as np
from google.oauth2.service_account import Credentials
from settings import load_settings

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
        
        # Load the settings
        self.settings = load_settings()

        # Define the scope
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file','https://www.googleapis.com/auth/drive']

        # Add your service account file
        creds = Credentials.from_service_account_file('auto-mmr-calculator-9676e1429d9a.json', scopes=scope)

        # Authorize the clientsheet
        client = gspread.authorize(creds)

        # Get the instance of the Spreadsheet
        sheet = client.open(self.settings['sheetname']) 

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

        # # Account for possible 6vs6 mode (12 players)
        # if self.mode == "5vs5":
        #     cell1 = self.TR_Tables.get("C97")[0][0]
        #     cell2 = self.TR_Tables.get("C105")[0][0]
        #     # If the cells are not empty, the mode is 6vs6
        #     if cell1 != "" and cell2 != "":
        #         self.mode = "6vs6"
            
        # Toggle flag for 32 track mode
        self.flag_32track = False

    def get_all(self):
        '''
        This method reads all the required data from the spreadsheet
        '''
        
        self.get_racers()
        self.get_scores()
        self.get_MMRs()

        if len(self.racers) != len(self.scores) or len(self.racers) != len(self.MMRs):
            raise ValueError("The number of racers, scores and MMRs do not match")
        
        self.calculate_placement()

        # Calculate the average MMR of the room
        self.average_room_MMR = np.average(self.LR_list) 

    def get_racers(self):
        '''
        This method returns the order of the racers
        '''

        match self.mode:
            case "FFA":
                racers = self.TR_Tables.get("B3:B14")
                self.racers = [value for sublist in racers for value in sublist]
            case "2vs2":
                racers = self.TR_Tables.get("B23:B39")
                self.racers = [value for sublist in racers for value in sublist if value != '']
            case "3vs3":
                racers = self.TR_Tables.get("B48:B62")
                self.racers = [value for sublist in racers for value in sublist if value != '']
            case "4vs4":
                racers = self.TR_Tables.get("B71:B84")
                self.racers = [value for sublist in racers for value in sublist if value != '']
            case "5vs5":
                racers = self.TR_Tables.get("B92:B104")
                self.racers = [value for sublist in racers for value in sublist if value != '']
            case "6vs6":
                racers = self.TR_Tables.get("B92:B104")
                self.racers = [value for sublist in racers for value in sublist if value != '']

        if len(self.racers) == 0:
            raise ValueError("No racers found in the sheet") 
        
        self.handle_new_players()

    def get_scores(self):
        '''
        This method returns the scores of the racers
        '''

        match self.mode:
            case "FFA":
                scores = self.TR_Tables.get("C3:C14")
                self.scores = [int(value) for sublist in scores for value in sublist]
            case "2vs2":
                scores = self.TR_Tables.get("C23:C39")
                self.scores = [int(value) for sublist in scores for value in sublist if value != '']
            case "3vs3":
                scores = self.TR_Tables.get("C48:C62")
                self.scores = [int(value) for sublist in scores for value in sublist if value != '']
            case "4vs4":
                scores = self.TR_Tables.get("C71:C84")
                self.scores = [int(value) for sublist in scores for value in sublist if value != '']
            case "5vs5":
                scores = self.TR_Tables.get("C92:C104")
                self.scores = [int(value) for sublist in scores for value in sublist if value != '']
            case "6vs6":
                scores = self.TR_Tables.get("C92:C104")
                self.scores = [int(value) for sublist in scores for value in sublist if value != '']

        if len(self.scores) == 0:
            raise ValueError("No scores found in the sheet")

    def get_MMRs(self):
        '''
        This method returns the MMRs of the racers
        '''

        match self.mode:
            case "FFA":
                MMRs = self.TR_Tables.get("E3:E14")
                self.MMRs = [value for sublist in MMRs for value in sublist]
            case "2vs2":
                MMRs = self.TR_Tables.get("E23:E39")
                self.MMRs = [value for sublist in MMRs for value in sublist if value != '']
            case "3vs3":
                MMRs = self.TR_Tables.get("E48:E62")
                self.MMRs = [value for sublist in MMRs for value in sublist if value != '']
            case "4vs4":
                MMRs = self.TR_Tables.get("E71:E84")
                self.MMRs = [value for sublist in MMRs for value in sublist if value != '']
            case "5vs5":
                MMRs = self.TR_Tables.get("E92:E104")
                self.MMRs = [value for sublist in MMRs for value in sublist if value != '']
            case "6vs6":
                MMRs = self.TR_Tables.get("E92:E104")
                self.MMRs = [value for sublist in MMRs for value in sublist if value != '']

        if len(self.MMRs) == 0:
            raise ValueError("No MMRs found in the sheet")
    
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
            for player in new_players:
                # Add to Playerdata
                # Find the first empty row in the Playerdata sheet
                playerdata_row = 2  # Assuming row 1 is headers
                while True:
                    if not self.Playerdata.cell(playerdata_row, 1).value:
                        break
                    playerdata_row += 1
                
                # Add player to Playerdata
                self.Playerdata.update_cell(playerdata_row, 1, player)  # Name
                self.Playerdata.update_cell(playerdata_row, 4, "???")   # MMR
                
                # Add to Placements
                # Find the first empty row in the Placements sheet
                placements_row = 5  # Start after header rows
                while self.Placements.cell(placements_row, 1).value is not None:
                    placements_row += 1
                
                # Add player to Placements
                self.Placements.update_cell(placements_row, 1, player)  # Name
                self.Placements.update_cell(placements_row, 2, "")      # Completion
                self.Placements.update_cell(placements_row, 8, "0")     # MMR Accumulation
            
            print(f"Added {len(new_players)} new player(s) to the sheets: {', '.join(new_players)}")

    def calculate_placement(self):
        '''
        This method assumes the MMR of unplaced racers and calculates their placements
        '''
        num = len(self.racers)
        MMRs = self.MMRs
        self.LR_list = []
        self.is_placed = []
        self.placement_updates = []
        self.completion= []

        averages = [] #debug list
    
        for i in range(num):
            # If the MMR is unknown
            if MMRs[i] == "???" or MMRs[i] == "":
                self.is_placed.append(False)
                # Get the name of the racer and their score
                racer = self.racers[i]
                points = [self.scores[i]]
                if self.flag_32track:
                    points[0] /= 2.67
    
                # Look for the racer in the placements
                location = self.Placements.find(racer)
    
                if location is None:
                    # Player has no prior placements
                    # Find the first empty row after the placed racers
                    j = 5
                    while self.Placements.cell(j,1).value is not None :
                        j += 1
    
                    row = j
                    self.completion.append("1/3")
                    self.placement_updates.append((row, 1, racer))
                    self.placement_updates.append((row, 2, "1/3"))
                    self.placement_updates.append((row, 4, points[0]))
    
                else:
                    row = location.row
                    completion = self.Placements.cell(row, 2).value
                    if completion is None:
                        self.completion.append("1/3")
                        self.placement_updates.append((row, 2, "1/3"))
                        self.placement_updates.append((row, 4, points[0]))
                        
                    if completion == "1/3":
                        self.completion.append("2/3")
                        self.placement_updates.append((row, 2, "2/3"))
                        self.placement_updates.append((row, 5, points[0]))
    
                        # Get the points of the previous event
                        points.append(int(self.Placements.cell(row,4).value))
                    
                    elif completion == "2/3":
                        self.completion.append("")
                        # This event places the racer
                        self.is_placed[i] = True

                        self.placement_updates.append((row, 2, "3/3"))
                        self.placement_updates.append((row, 6, points[0]))
    
                        # Get the points of the previous events
                        points.append(int(self.Placements.cell(row,4).value))
                        points.append(int(self.Placements.cell(row,5).value))
    
                # Calculate the average number of points in the past event(s)
                average = np.average(points)
                averages.append(average) #debug list

                # Calculate the MMR of the racer based on the average
                for threshold, mmr in MMR_THRESHOLDS.items():
                    if average < threshold:
                        MMR = mmr
                        break
                else:
                    MMR = 7750

                if completion == "2/3":
                    # MMR is average with previous season MMR

                    # Get the previous season MMR
                    row_playerdata = self.Playerdata.find(racer).row
                    previous_season_MMR = self.Playerdata.cell(row_playerdata, 11).value

                    if previous_season_MMR is not None and previous_season_MMR != "???":
                        previous_season_MMR = int(previous_season_MMR)
                        MMR = (MMR + previous_season_MMR) / 2
    
                # Add previously gained MMR to the new MMR
                temp = self.Placements.cell(row,8).value
                MMR += int(temp) if temp is not None else 0
                self.LR_list.append(MMR)
            else:
                self.is_placed.append(True)
                self.completion.append("")
                self.LR_list.append(int(MMRs[i]))

        print(averages) #debug list
    
    def update_placements(self):
        '''
        This method updates the cells in the placements based on the calculations made in calculate_placement
        '''
        cell_list = []
        for row, column, value in self.placement_updates:
            cell_list.append(gspread.models.Cell(row, column, value))
        self.Placements.update_cells(cell_list)

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
        # insert the correct number of players into the sheet
        num_players = len(self.racers)
        self.Table_stuff.update("C1", [[self.mode]])
        self.Table_stuff.update("C2", [[num_players]])

        # get the right k values depending on the mode
        match self.mode:
            case "FFA":
                k_list = self.Table_stuff.get("E11:E22")
            case "2vs2":
                k_list = self.Table_stuff.get("F11:F16")
            case "3vs3":
                k_list = self.Table_stuff.get("G11:G14")
            case "4vs4":
                k_list = self.Table_stuff.get("H11:H13")
            case "5vs5":
                k_list = self.Table_stuff.get("I11:I12")
            case "6vs6":
                k_list = self.Table_stuff.get("I11:I12")
        
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
        
        # Round the MMR changes to the nearest integer
        self.delta_MMRs = [int(round(delta_MMR)) for delta_MMR in self.delta_MMRs]

        # add the change in MMR to the old MMR
        self.MMR_new = np.add(self.LR_list, self.delta_MMRs)

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

    def update_sheet(self):
        '''
        This method updates the MMRs of the players on the sheet
        '''
        # Loop through the placements and update the cells
        for row, column, value in self.placement_updates:
            self.Placements.update_cell(row, column, value)
        
        # Loop through the racers and update their MMR
        for i in range(len(self.racers)):
            
            # Get the row of the racer
            row = self.Playerdata.find(self.racers[i]).row

            # Skip the unplaced racers as their MMR should not be updated
            if not self.is_placed[i]:
                continue
            
            # Update the MMR of the racer
            self.Playerdata.update_cell(row, 4, int(self.MMR_new[i]))
            
    def update_placements_MMR(self):
        '''
        This method updates the MMR of the racers in the placements sheet
        '''
        for i in range(len(self.racers)):
            if not self.is_placed[i]:
                # Get the row of the racer
                row = self.Placements.find(self.racers[i]).row

                # Update the MMR of the racer
                old_MMR = int(self.Placements.cell(row, 8).value) if self.Placements.cell(row, 8).value is not None else 0
                self.Placements.update_cell(row, 8, old_MMR + int(self.delta_MMRs[i]))

    def clear_table(self):
        '''
        This method clears the TR tables
        '''

        # Clear the Player, Score and Change columns

        match self.mode:
            case "FFA":
                self.TR_Tables.update("B3:B14", [[""] for _ in range(12)])
                self.TR_Tables.update("C3:C14", [[""] for _ in range(12)])
                self.TR_Tables.update("F3:F14", [[""] for _ in range(12)])
                self.TR_Tables.update("H3:H14", [["-"] for _ in range(12)])
                self.TR_Tables.update("I3:I14", [[""] for _ in range(12)])
            case "2vs2":
                self.TR_Tables.update("B23:B39", [[""] for _ in range(17)])
                self.TR_Tables.update("C23:C39", [[""] for _ in range(17)])
                self.TR_Tables.update("F23:F39", [[""] for _ in range(17)])
                self.TR_Tables.update("H23:H39", [["-"] for _ in range(17)])
                self.TR_Tables.update("I23:I39", [[""] for _ in range(17)])
            case "3vs3":
                self.TR_Tables.update("B48:B62", [[""] for _ in range(15)])
                self.TR_Tables.update("C48:C62", [[""] for _ in range(15)])
                self.TR_Tables.update("F48:F62", [[""] for _ in range(15)])
                self.TR_Tables.update("H48:H62", [["-"] for _ in range(15)])
                self.TR_Tables.update("I48:I62", [[""] for _ in range(15)])
            case "4vs4":
                self.TR_Tables.update("B71:B84", [[""] for _ in range(14)])
                self.TR_Tables.update("C71:C84", [[""] for _ in range(14)])
                self.TR_Tables.update("F71:F84", [[""] for _ in range(14)])
                self.TR_Tables.update("H71:H84", [["-"] for _ in range(14)])
                self.TR_Tables.update("I71:I84", [[""] for _ in range(14)])
            case "5vs5":
                self.TR_Tables.update("B92:B104", [[""] for _ in range(13)])
                self.TR_Tables.update("C92:C104", [[""] for _ in range(13)])
                self.TR_Tables.update("F92:F104", [[""] for _ in range(13)])
                self.TR_Tables.update("H92:H104", [["-"] for _ in range(13)])
                self.TR_Tables.update("I92:I104", [[""] for _ in range(13)])
            case "6vs6":
                self.TR_Tables.update("B92:B104", [[""] for _ in range(13)])
                self.TR_Tables.update("C92:C104", [[""] for _ in range(13)])
                self.TR_Tables.update("F92:F104", [[""] for _ in range(13)])
                self.TR_Tables.update("H92:H104", [["-"] for _ in range(13)])
                self.TR_Tables.update("I92:I104", [[""] for _ in range(113)])

    def LTRC_routine(self):
        self.get_all()
        self.find_ranking()
        self.find_k_values()
        self.calc_new_MMR()
        
if __name__ == "__main__":
    # LTRC = LTRC_manager()
    # LTRC.LTRC_routine()

    # LTRC.fill_MMR_change_table()
    # LTRC.update_placements_MMR()
    # # LTRC.update_sheet()

    # print(f"Mode: {LTRC.mode}")
    # print(f"Racers: {LTRC.racers}")
    # print(f"Old MMRs: {LTRC.LR_list}")
    # print(f"Change in MMR: {LTRC.delta_MMRs}")
    # # print(f"New MMRs: {LTRC.MMR_new}")

    print("Don't run this script you big dummy!")