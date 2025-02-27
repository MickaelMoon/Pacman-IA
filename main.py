from random import choice, random
import arcade
import os
import pickle
import matplotlib.pyplot as plt
import collections

###############################################################################
# Nouvelle map (Pacman)
###############################################################################

MAZE = """
xxxxxxxxxxx
xo.......ox
x.xxx.xxx.x
x.x.....x.x
x.x.x.x.x.x
x...x.x...x
x.x.xxx.x.x
x.x.....x.x
x.xxx.xxx.x
xo.......ox
xxxxxxxxxxx
"""

FILE_AGENT = 'mouse.qtable'

# Constantes pour le labyrinthe
TILE_WALL = 'x'
TILE_PELLET = '.'
TILE_POWER_PELLET = 'o'

# Actions
ACTION_UP = 'U'
ACTION_DOWN = 'D'
ACTION_LEFT = 'L'
ACTION_RIGHT = 'R'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT]

# Déplacements
MOVES = {
    ACTION_UP: (-1, 0),
    ACTION_DOWN: (1, 0),
    ACTION_LEFT: (0, -1),
    ACTION_RIGHT: (0, 1)
}

# Récompenses
REWARD_OUT     = -100       # Sortie du labyrinthe
REWARD_WALL    = -100       # Collision avec un mur
REWARD_REPEAT  = -1         # Malus pour revisiter une case
REWARD_WIN     = 10000      # Récompense de victoire (tous les pellets ramassés)
REWARD_PELLET  = 50         # Ramasser un pellet
REWARD_DEFAULT = -1         # Mouvement "normal" (adoucit pour un labyrinthe plus vaste)
REWARD_GHOST   = -10000     # Collision avec le fantôme

WIN = 1
LOOSE = 0

# Paramètre graphique
SPRITE_SIZE = 64

###############################################################################
# Fonction utilitaire pour le Q-Learning
###############################################################################

def arg_max(table):
    """Retourne l'action associée à la valeur maximale dans le dictionnaire."""
    return max(table, key=table.get)

###############################################################################
# QTable : stockage et mise à jour de la Q-table
###############################################################################

class QTable:
    def __init__(self, learning_rate=0.1, discount_factor=0.9):
        self.dic = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def set(self, state, action, reward, new_state):
        if state not in self.dic:
            self.dic[state] = {a: 0 for a in ACTIONS}
        if new_state not in self.dic:
            self.dic[new_state] = {a: 0 for a in ACTIONS}
        old_value = self.dic[state][action]
        max_next = max(self.dic[new_state].values())
        # Formule de mise à jour Q-learning
        delta = reward + self.discount_factor * max_next - old_value
        self.dic[state][action] = old_value + self.learning_rate * delta

    def best_action(self, state):
        if state in self.dic:
            return arg_max(self.dic[state])
        else:
            return choice(ACTIONS)

    def __repr__(self):
        res = ' ' * 11
        for action in ACTIONS:
            res += f'{action:5s}'
        res += '\n'
        for state in self.dic:
            res += str(state) + " "
            for action in self.dic[state]:
                res += f"{self.dic[state][action]:5.1f}"
            res += '\n'
        return res

###############################################################################
# Agent
###############################################################################

class Agent:
    def __init__(self, env, exploration=1.0, exploration_decay=0.995):
        self.env = env
        self.history = []
        self.score = None
        self.qtable = QTable(learning_rate=0.1, discount_factor=0.9)
        self.exploration = exploration
        self.exploration_decay = exploration_decay
        self.reset()

    def reset(self):
        if self.score is not None:
            self.history.append(self.score)
        self.position = self.env.start
        self.score = 0
        self.env.reset_maze()

    def shake(self, exploration=1.0):
        """Réinitialise l'exploration (par exemple, lors d'un appui sur E)."""
        self.exploration = exploration

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump((self.qtable.dic, self.history), file)

    def load(self, filename):
        with open(filename, 'rb') as file:
            self.qtable.dic, self.history = pickle.load(file)

    def do(self, action=None):
        """
        Exécute une action, met à jour la Q-table et retourne (action, reward).
        Utilise une vision de taille 5x5.
        """
        current_vision = self.env.get_vision(self.position, vision_size=5)
        current_state = (
            tuple(tuple(row) for row in current_vision),
            self.env.closest_pellet(self.position),
            self.env.distance_to_ghost(self.position)
        )
        if action is None:
            action = self.best_action()
        # Déplacement de Pac-Man
        new_position, reward = self.env.move(self.position, action)
        self.position = new_position
        self.score += reward
        # Déplacement du fantôme (pour que le nouvel état soit à jour)
        self.env.move_ghost(self.position)
        new_vision = self.env.get_vision(self.position, vision_size=5)
        new_state = (
            tuple(tuple(row) for row in new_vision),
            self.env.closest_pellet(self.position),
            self.env.distance_to_ghost(self.position)
        )
        self.qtable.set(current_state, action, reward, new_state)
        return action, reward

    def best_action(self):
        current_vision = self.env.get_vision(self.position, vision_size=5)
        current_state = (
            tuple(tuple(row) for row in current_vision),
            self.env.closest_pellet(self.position),
            self.env.distance_to_ghost(self.position)
        )
        if random() < self.exploration:
            self.exploration *= self.exploration_decay
            return choice(ACTIONS)
        else:
            return self.qtable.best_action(current_state)

    def __repr__(self):
        return f"{self.position} score:{self.score:.1f} exploration:{self.exploration:.3f}"

###############################################################################
# Gestion des pellets
###############################################################################

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

###############################################################################
# Environnement
###############################################################################

class Environment:
    def __init__(self, text, start=(1, 1), ghost_start=(9, 7)):
        rows = text.strip().split('\n')
        self.height = len(rows)
        self.width = len(rows[0])
        self.maze = {}
        self.start = start
        self.ghost_start = ghost_start
        self.ghost_position = ghost_start
        self.visited_positions = set()
        for i in range(self.height):
            for j in range(self.width):
                self.maze[(i, j)] = rows[i][j]
        self.pellet_manager = PelletManager(self.maze)

    def distance_to_ghost(self, position):
        """
        Retourne un tuple (haut, droite, bas, gauche) indiquant
        la distance du fantôme à Pac-Man.
        """
        ghost = self.ghost_position
        vertical_distance = ghost[0] - position[0]
        horizontal_distance = ghost[1] - position[1]
        distances = [0, 0, 0, 0] 
        if vertical_distance < 0:
            distances[0] = abs(vertical_distance)
        elif vertical_distance > 0:
            distances[2] = abs(vertical_distance)
        if horizontal_distance > 0:
            distances[1] = abs(horizontal_distance)
        elif horizontal_distance < 0:
            distances[3] = abs(horizontal_distance)
        return tuple(distances)

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

    def reset_maze(self):
        rows = MAZE.strip().split('\n')
        for i in range(self.height):
            for j in range(self.width):
                self.maze[(i, j)] = rows[i][j]
        self.pellet_manager.reset_pellets()
        self.ghost_position = self.ghost_start
        self.visited_positions = set()

    def move_ghost(self, pacman_position):
        """
        Déplace le fantôme vers Pac-Man en utilisant une recherche en largeur (BFS).
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
        path = bfs(self.ghost_position, pacman_position)
        if len(path) > 1:
            self.ghost_position = path[1]

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
        elif new_position == self.ghost_position:
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

###############################################################################
# Fenêtre (affichage avec Arcade)
###############################################################################

class MazeWindow(arcade.Window):
    def __init__(self, agent):
        super().__init__(SPRITE_SIZE * agent.env.width,
                         SPRITE_SIZE * agent.env.height,
                         "Pacman AI")
        self.agent = agent
        self.env = agent.env
        arcade.set_background_color(arcade.color.BLACK)
        self.set_update_rate(1 / 1200)

    def setup(self):
        self.walls = arcade.SpriteList()
        self.pellets = arcade.SpriteList()

        # Chargement des murs et pellets depuis la map
        for (i, j), tile in self.env.maze.items():
            if tile == TILE_WALL:
                sprite = self.create_sprite('assets/wall.png', (i, j))
                self.walls.append(sprite)
            elif tile == TILE_PELLET:
                sprite = self.create_sprite('assets/pellet.png', (i, j))
                self.pellets.append(sprite)
            elif tile == TILE_POWER_PELLET:
                sprite = self.create_sprite('assets/power_pellet.png', (i, j))
                self.pellets.append(sprite)

        self.player = self.create_sprite('assets/pacman.png', self.agent.position)
        self.ghost = self.create_sprite('assets/ghost.png', self.env.ghost_position)

    def create_sprite(self, resource, state):
        sprite = arcade.Sprite(resource, 0.5)
        sprite.center_x = (state[1] + 0.5) * SPRITE_SIZE
        sprite.center_y = (self.env.height - state[0] - 0.5) * SPRITE_SIZE
        return sprite

    def on_draw(self):
        arcade.start_render()
        self.walls.draw()
        self.pellets.draw()
        self.player.draw()
        self.ghost.draw()
        arcade.draw_text(f'{self.agent}', 10, 10, arcade.csscolor.WHITE, 20)

    def on_update(self, delta_time):
        if (not self.env.pellet_manager.are_all_pellets_collected() and
            self.agent.position != self.env.ghost_position):
            self.agent.do()

            # Suppression du sprite de pellet mangé
            for pellet in self.pellets:
                if (pellet.center_x, pellet.center_y) == (
                    (self.agent.position[1] + 0.5) * SPRITE_SIZE,
                    (self.env.height - self.agent.position[0] - 0.5) * SPRITE_SIZE
                ):
                    self.pellets.remove(pellet)
                    break

            self.player.center_x = (self.agent.position[1] + 0.5) * SPRITE_SIZE
            self.player.center_y = (self.env.height - self.agent.position[0] - 0.5) * SPRITE_SIZE
            self.ghost.center_x = (self.env.ghost_position[1] + 0.5) * SPRITE_SIZE
            self.ghost.center_y = (self.env.height - self.env.ghost_position[0] - 0.5) * SPRITE_SIZE
        else:
            print(f"Score: {self.agent.score}")
            self.agent.reset()
            self.setup()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.agent.reset()
            self.setup()
        elif key == arcade.key.E:
            self.agent.shake()
        elif key == arcade.key.D:
            self.agent.exploration = 0.0

###############################################################################
# Main
###############################################################################

if __name__ == "__main__":
    env = Environment(MAZE, start=(1, 1), ghost_start=(9, 7))
    agent = Agent(env, exploration=1.0, exploration_decay=0.999)

    if os.path.exists(FILE_AGENT):
        agent.load(FILE_AGENT)

    window = MazeWindow(agent)
    window.setup()
    arcade.run()

    agent.save(FILE_AGENT)

    plt.plot(agent.history)
    plt.title("Score history")
    plt.xlabel("Episodes")
    plt.ylabel("Score")
    plt.show()