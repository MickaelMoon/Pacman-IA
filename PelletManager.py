###############################################################################
# Gestion des pellets
###############################################################################

from constante import TILE_PELLET, TILE_POWER_PELLET


class PelletManager:
    def __init__(self, maze):
        self.original_maze = maze
        self.reset_pellets()

    def reset_pellets(self):
        self.pellets = {
            position for position, tile in self.original_maze.items()
            if tile in [TILE_PELLET, TILE_POWER_PELLET]
        }

    def collect_pellet(self, position):
        if position in self.pellets:
            self.pellets.remove(position)

    def are_all_pellets_collected(self):
        return len(self.pellets) == 0
