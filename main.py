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
xxxxxxxxxxxxxxxxx
xo.............ox
x.xxx.xxxxx.xxx.x
x.x...........x.x
x.x.xxx.x.xxx.x.x
x...x.....x...x.x
x.x.x.xxxxx.x.x.x
x.x...........x.x
x.xxx.xxxxx.xxx.x
x.x...........x.x
x.x.xxx.x.xxx.x.x
x...x.....x...x.x
x.x.x.xxxxx.x.x.x
x.x...........x.x
x.xxx.xxxxx.xxx.x
xo.............ox
xxxxxxxxxxxxxxxxx
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
REWARD_OUT     = -500       # Sortie du labyrinthe
REWARD_WALL    = -200       # Collision avec un mur
REWARD_REPEAT  = -5         # Malus pour revisiter une case
REWARD_WIN     = 500000     # Récompense de victoire (tous les pellets ramassés)
REWARD_PELLET  = 5000       # Ramasser un pellet (increased reward)
REWARD_DEFAULT = -2         # Mouvement "normal" (adoucit pour un labyrinthe plus vaste)
REWARD_GHOST   = -100000    # Collision avec le fantôme
REWARD_EAT_GHOST = 20000     # Reward for eating a ghost
POWER_PELLET_DURATION = 40   # How many moves power pellet lasts

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
    def __init__(self, learning_rate=0.2, discount_factor=0.95):
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
    def __init__(self, env, exploration=1.0, exploration_decay=0.99995):
        self.env = env
        self.history = []
        self.score = None
        self.qtable = QTable(learning_rate=0.3, discount_factor=0.99)
        self.exploration = exploration
        self.exploration_decay = exploration_decay
        self.last_action = None
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
            self.env.distance_to_ghosts(self.position)
        )
        if action is None:
            action = self.best_action()
        self.last_action = action
        # Déplacement de Pac-Man
        new_position, reward = self.env.move(self.position, action)
        self.position = new_position
        self.score += reward
        # Déplacement des fantômes (pour que le nouvel état soit à jour)
        self.env.move_ghosts(self.position, self.last_action)
        new_vision = self.env.get_vision(self.position, vision_size=5)
        new_state = (
            tuple(tuple(row) for row in new_vision),
            self.env.closest_pellet(self.position),
            self.env.distance_to_ghosts(self.position)
        )
        self.qtable.set(current_state, action, reward, new_state)
        return action, reward

    def best_action(self):
        current_vision = self.env.get_vision(self.position, vision_size=5)
        current_state = (
            tuple(tuple(row) for row in current_vision),
            self.env.closest_pellet(self.position),
            self.env.distance_to_ghosts(self.position)
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
    def __init__(self, text, start=(1, 1), ghost_starts=[(15, 1), (15, 15), (1, 15), (8, 8)]):
        rows = text.strip().split('\n')
        self.height = len(rows)
        self.width = len(rows[0])
        self.maze = {}
        self.start = start
        self.ghost_starts = ghost_starts
        self.ghost_positions = list(ghost_starts)
        self.visited_positions = set()
        self.power_pellet_active = 0
        self.eaten_ghosts = set()
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
        self.power_pellet_active = 0
        self.eaten_ghosts = set()

    def move_ghosts(self, pacman_position, pacman_last_action):
        """
        Implements the four classic ghost behaviors:
        - Blinky (Red): Directly targets Pacman
        - Pinky (Pink): Targets 4 tiles ahead of Pacman
        - Inky (Cyan): Uses Blinky's position and Pacman's position
        - Clyde (Orange): Targets Pacman when far, runs away when close
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

        if self.power_pellet_active > 0:
        # Scared ghost behavior
            for i, ghost_pos in enumerate(self.ghost_positions):
                if i in self.eaten_ghosts:
                    continue
                # Run away from Pacman
                scatter_points = [(1, 1), (1, 15), (15, 1), (15, 15)]
                path = bfs(ghost_pos, scatter_points[i])
                if len(path) > 1:
                    self.ghost_positions[i] = path[1]
            return 
        # Blinky (Red Ghost) - Direct chase

        distance_to_pacman = abs(self.ghost_positions[0][0] - pacman_position[0]) + \
                            abs(self.ghost_positions[0][1] - pacman_position[1])
        
        if distance_to_pacman > 6:  # Only chase when far away
            path = bfs(self.ghost_positions[0], pacman_position)
        else:
            # Move to scatter mode when close to Pacman
            scatter_point = (1, 15)  # Top-left corner
            path = bfs(self.ghost_positions[0], scatter_point)
        
        if len(path) > 1:
            self.ghost_positions[0] = path[1]


        # Pinky (Pink Ghost) - Ambush 4 tiles ahead
        pacman_direction = MOVES[pacman_last_action]
        pinky_target = (
            pacman_position[0] + 4 * pacman_direction[0],
            pacman_position[1] + 4 * pacman_direction[1]
        )
        path = bfs(self.ghost_positions[1], pinky_target)
        if len(path) > 1:
            self.ghost_positions[1] = path[1]

        # Inky (Cyan Ghost) - Uses Blinky's position
        blinky_position = self.ghost_positions[0]
        inky_vector = (
            pacman_position[0] + 2 * pacman_direction[0] - blinky_position[0],
            pacman_position[1] + 2 * pacman_direction[1] - blinky_position[1]
        )
        inky_target = (
            blinky_position[0] + inky_vector[0],
            blinky_position[1] + inky_vector[1]
        )
        path = bfs(self.ghost_positions[2], inky_target)
        if len(path) > 1:
            self.ghost_positions[2] = path[1]

        # Clyde (Orange Ghost) - Scatter when close
        distance_to_pacman = abs(self.ghost_positions[3][0] - pacman_position[0]) + \
                    abs(self.ghost_positions[3][1] - pacman_position[1])
        if distance_to_pacman > 8: 
            path = bfs(self.ghost_positions[3], pacman_position)
        else:
            scatter_point = (15, 15)
            path = bfs(self.ghost_positions[3], scatter_point)
        if len(path) > 1:
            self.ghost_positions[3] = path[1]

    def move(self, position, action):
        move = MOVES[action]
        new_position = (position[0] + move[0], position[1] + move[1])
        reward = 0
    
        if new_position not in self.maze:
            reward += REWARD_OUT
        elif self.maze[new_position] == TILE_WALL:
            reward += REWARD_WALL
        elif new_position in self.ghost_positions:
            ghost_index = self.ghost_positions.index(new_position)
            if self.power_pellet_active > 0 and ghost_index not in self.eaten_ghosts:
                # Eat ghost
                reward += REWARD_EAT_GHOST
                self.eaten_ghosts.add(ghost_index)
                self.ghost_positions[ghost_index] = self.ghost_starts[ghost_index]
                position = new_position
            else:
                reward += REWARD_GHOST
                position = new_position
        elif self.maze[new_position] in [TILE_PELLET, TILE_POWER_PELLET]:
            if self.maze[new_position] == TILE_POWER_PELLET:
                self.power_pellet_active = POWER_PELLET_DURATION
                self.eaten_ghosts = set()
            reward += REWARD_PELLET
            position = new_position
            self.maze[new_position] = ' '
            self.pellet_manager.collect_pellet(position)
            if self.pellet_manager.are_all_pellets_collected():
                reward += REWARD_WIN
                print("WIN")
        else:
            reward += REWARD_DEFAULT
            position = new_position
    
        # Decrease power pellet timer
        if self.power_pellet_active > 0:
            self.power_pellet_active -= 1
    
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
        self.ghosts = arcade.SpriteList()

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
        ghost_sprites = ['assets/ghost.png', 'assets/ghost2.png', 
                        'assets/ghost3.png', 'assets/ghost4.png']
        for i, ghost_position in enumerate(self.env.ghost_positions):
            ghost = self.create_sprite(ghost_sprites[i], ghost_position)
            self.ghosts.append(ghost)

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
        self.ghosts.draw()
        arcade.draw_text(f'{self.agent}', 10, 10, arcade.csscolor.WHITE, 20)

        for i, ghost in enumerate(self.ghosts):
            if self.env.power_pellet_active > 0 and i not in self.env.eaten_ghosts:
                ghost.color = arcade.color.BLUE
            else:
                ghost.color = arcade.color.WHITE
            ghost.draw()

        if self.env.power_pellet_active > 0:
            arcade.draw_text(f'Power: {self.env.power_pellet_active}', 
                           10, 40, arcade.csscolor.WHITE, 20)
        arcade.draw_text(f'{self.agent}', 10, 10, arcade.csscolor.WHITE, 20)

    def on_update(self, delta_time):
        if (not self.env.pellet_manager.are_all_pellets_collected() and
            self.agent.position not in self.env.ghost_positions):
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
            for i, ghost in enumerate(self.ghosts):
                ghost.center_x = (self.env.ghost_positions[i][1] + 0.5) * SPRITE_SIZE
                ghost.center_y = (self.env.height - self.env.ghost_positions[i][0] - 0.5) * SPRITE_SIZE
        else:
            #TOTOprint(f"Score: {self.agent.score}")
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
    env = Environment(MAZE, start=(1, 1), 
                     ghost_starts=[(15,15), (15, 1), (1, 15), (8, 8)])
    agent = Agent(env, exploration=1.0, exploration_decay=0.99998)
    episode_count = 0
    max_episodes = 10000000  # Set maximum episodes

    if os.path.exists(FILE_AGENT):
        agent.load(FILE_AGENT)

    window = MazeWindow(agent)
    window.setup()

    # Add progress tracking
    def update(dt):
        global episode_count
        if episode_count % 1000 == 0:
            print(f"Episode {episode_count}, Score: {agent.score:.1f}, Exploration: {agent.exploration:.3f}")
        if episode_count >= max_episodes:
            arcade.close_window()
        episode_count += 1

    arcade.schedule(update, 1/60)
    arcade.run()

    agent.save(FILE_AGENT)

    plt.plot(agent.history)
    plt.title(f"Score history ({episode_count} episodes)")
    plt.xlabel("Episodes")
    plt.ylabel("Score")
    plt.show()