from MMR import LTRC_manager

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