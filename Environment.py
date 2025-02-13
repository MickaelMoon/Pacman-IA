###############################################################################
# Environnement
###############################################################################

import collections
from PelletManager import PelletManager
from constante import *


class Environment:
    def __init__(self, text, start=(1, 1), ghost_starts=[(9, 7), (1, 9)]):
        rows = text.strip().split('\n')
        self.height = len(rows)
        self.width = len(rows[0])
        self.maze = {}
        self.start = start
        self.ghost_starts = ghost_starts
        self.ghost_positions = list(ghost_starts)
        self.visited_positions = set()
        for i in range(self.height):
            for j in range(self.width):
                self.maze[(i, j)] = rows[i][j]
        self.pellet_manager = PelletManager(self.maze)

    def distance_to_ghosts(self, position):
        """
        Retourne un tuple (haut, droite, bas, gauche) indiquant
        la distance des fantômes à Pac-Man.
        """
        distances = [float('inf')] * 4
        for ghost in self.ghost_positions:
            vertical_distance = ghost[0] - position[0]
            horizontal_distance = ghost[1] - position[1]
            if vertical_distance < 0:
                distances[0] = min(distances[0], abs(vertical_distance))
            elif vertical_distance > 0:
                distances[2] = min(distances[2], abs(vertical_distance))
            if horizontal_distance > 0:
                distances[1] = min(distances[1], abs(horizontal_distance))
            elif horizontal_distance < 0:
                distances[3] = min(distances[3], abs(horizontal_distance))
        distances = [0 if d == float('inf') else d for d in distances]
        return tuple(distances)

    def reset_maze(self):
        rows = MAZE.strip().split('\n')
        for i in range(self.height):
            for j in range(self.width):
                self.maze[(i, j)] = rows[i][j]
        self.pellet_manager.reset_pellets()
        self.ghost_positions = list(self.ghost_starts)
        self.visited_positions = set()

    def move_ghosts(self, pacman_position, pacman_last_action):
        """
        Déplace les fantômes vers Pac-Man en utilisant différentes stratégies.
        """
        def bfs(start, goal):
            queue = collections.deque([[start]])
            seen = {start}
            while queue:
                path = queue.popleft()
                x, y = path[-1]
                if (x, y) == goal:
                    return path
                for move in MOVES.values():
                    nx, ny = x + move[0], y + move[1]
                    if (nx, ny) in self.maze and self.maze[(nx, ny)] != TILE_WALL and (nx, ny) not in seen:
                        queue.append(path + [(nx, ny)])
                        seen.add((nx, ny))
            return []

        # Blinky (Red Ghost) - Directly targets Pac-Man's current position
        path = bfs(self.ghost_positions[0], pacman_position)
        if len(path) > 1:
            self.ghost_positions[0] = path[1]

        # Inky (Cyan Ghost) - Uses both Blinky's position and Pac-Man's position
        blinky_position = self.ghost_positions[0]
        pacman_direction = MOVES[pacman_last_action]
        vector = (pacman_position[0] + 2 * pacman_direction[0] - blinky_position[0],
                  pacman_position[1] + 2 * pacman_direction[1] - blinky_position[1])
        target_position = (blinky_position[0] + vector[0], blinky_position[1] + vector[1])
        path = bfs(self.ghost_positions[1], target_position)
        if len(path) > 1:
            self.ghost_positions[1] = path[1]

    def move(self, position, action):
        """
        Effectue le mouvement de Pac-Man selon l'action choisie et retourne
        (nouvelle_position, reward).
        """
        move = MOVES[action]
        new_position = (position[0] + move[0], position[1] + move[1])
        reward = 0

        if new_position not in self.maze:
            reward += REWARD_OUT
        elif self.maze[new_position] == TILE_WALL:
            reward += REWARD_WALL
        elif new_position in self.ghost_positions:
            reward += REWARD_GHOST
            position = new_position
        elif self.maze[new_position] in [TILE_PELLET, TILE_POWER_PELLET]:
            reward += REWARD_PELLET
            position = new_position
            self.maze[new_position] = ' '  # On enlève le pellet
            self.pellet_manager.collect_pellet(position)
            if self.pellet_manager.are_all_pellets_collected():
                reward += REWARD_WIN
                print("WIN")
        else:
            reward += REWARD_DEFAULT
            position = new_position

        if position in self.visited_positions:
            reward += REWARD_REPEAT
        else:
            self.visited_positions.add(position)

        return position, reward
    
    def closest_pellet(self, position):
        """
        Retourne, pour chaque direction (haut, droite, bas, gauche),
        la distance minimale jusqu'à un pellet.
        """
        min_distances = [float('inf')] * 4
        for pellet in self.pellet_manager.pellets:
            vertical_distance = pellet[0] - position[0]
            horizontal_distance = pellet[1] - position[1]
            if vertical_distance < 0:
                min_distances[0] = min(min_distances[0], abs(vertical_distance))
            elif vertical_distance > 0:
                min_distances[2] = min(min_distances[2], abs(vertical_distance))
            if horizontal_distance > 0:
                min_distances[1] = min(min_distances[1], abs(horizontal_distance))
            elif horizontal_distance < 0:
                min_distances[3] = min(min_distances[3], abs(horizontal_distance))
        min_distances = [0 if d == float('inf') else d for d in min_distances]
        return tuple(min_distances)
    
    def get_vision(self, position, vision_size=3):
        """
        Retourne une matrice (de taille vision_size x vision_size) représentant
        la vue autour de la position. On retourne 'x' pour les positions hors du labyrinthe.
        """
        radius = vision_size // 2
        vision = []
        for i in range(-radius, radius + 1):
            row = []
            for j in range(-radius, radius + 1):
                pos = (position[0] + i, position[1] + j)
                row.append(self.maze.get(pos, 'x'))
            vision.append(row)
        return vision

