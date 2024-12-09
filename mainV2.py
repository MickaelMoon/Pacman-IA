from random import *
import arcade
import os
import pickle
import matplotlib.pyplot as plt
import collections

MAZE = """
xxxxxxxxx
xo.....ox
x.xx.xx.x
x.x...x.x
x.x.x.x.x
x.x.x.x.x
x.x...x.x
x.xx.xx.x
xo.....ox
xxxxxxxxx
"""

FILE_AGENT = 'mouse.qtable'

TILE_WALL = 'x'
TILE_PELLET = '.'
TILE_POWER_PELLET = 'o'

ACTION_UP = 'U'
ACTION_DOWN = 'D'
ACTION_LEFT = 'L'
ACTION_RIGHT = 'R'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT]
REWARD_OUT = -100
REWARD_WALL = -100
REWARD_WIN = 1000
REWARD_PELLET = 10
REWARD_DEFAULT = -1
REWARD_GHOST = -1000

WIN = 1
LOOSE = 0

SPRITE_SIZE = 64

MOVES = {ACTION_UP: (-1, 0),
         ACTION_DOWN: (1, 0),
         ACTION_LEFT: (0, -1),
         ACTION_RIGHT: (0, 1)}


def arg_max(table):
    return max(table, key=table.get)


class QTable:
    def __init__(self, learning_rate=0.7, discount_factor=0.95):
        self.dic = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def set(self, state, action, reward, new_state):
        """Met à jour la Q-table en fonction des états (vision) et des actions."""
        # Si l'état ou le nouvel état n'est pas déjà dans la table, initialisez-les
        if state not in self.dic:
            self.dic[state] = {ACTION_UP: 0, ACTION_DOWN: 0, ACTION_LEFT: 0, ACTION_RIGHT: 0}
        if new_state not in self.dic:
            self.dic[new_state] = {ACTION_UP: 0, ACTION_DOWN: 0, ACTION_LEFT: 0, ACTION_RIGHT: 0}

        # Calcul du delta et mise à jour
        delta = reward + self.discount_factor * max(self.dic[new_state].values()) - self.dic[state][action]
        self.dic[state][action] += self.learning_rate * delta
        # Q(s, a) = Q(s, a) + alpha * [reward + gamma * max(S', a) - Q(s, a)]

    def best_action(self, position):
        if position in self.dic:
            return arg_max(self.dic[position])
        else:
            return choice(ACTIONS)

    def __repr__(self):
        res = ' ' * 11
        for action in ACTIONS:
            res += f'{action:5s}'
        res += '\r\n'
        for state in self.dic:
            res += str(state) + " "
            for action in self.dic[state]:
                res += f"{self.dic[state][action]:5d}"
            res += '\r\n'
        return res


class Agent:
    def __init__(self, env):
        self.env = env
        self.history = []
        self.score = None
        self.collected_pellets = 0
        self.reset()
        self.qtable = QTable()
        self.exploration = 0

    def reset(self):
        if self.score:
            self.history.append(self.score)
        self.position = self.env.start  # Utilise la position définie
        self.score = 0
        self.collected_pellets = 0
        self.env.reset_maze()

    def shake(self, exploration=1.0):
        self.exploration = 1.0

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump((self.qtable.dic, self.history), file)

    def load(self, filename):
        with open(filename, 'rb') as file:
            self.qtable.dic, self.history = pickle.load(file)

    def do(self, action=None):
        # Obtenir la vision actuelle (état)
        current_vision = self.env.get_vision(self.position)
        current_state = tuple(tuple(row) for row in current_vision)

        # Choisir l'action
        if not action:
            action = self.best_action()

        # Effectuer l'action
        new_position, reward = self.env.move(self.position, action)

        # Obtenir la nouvelle vision (nouvel état)
        new_vision = self.env.get_vision(new_position)
        new_state = tuple(tuple(row) for row in new_vision)

        # Mettre à jour la Q-table
        self.qtable.set(current_state, action, reward, new_state)

        # Mettre à jour la position et le score
        self.position = new_position
        self.score += reward

        return action, reward

    def best_action(self):
        """Choisit la meilleure action en fonction de l'état (basé sur la vision)."""
        vision = self.env.get_vision(self.position)  # Récupérer la vision actuelle
        vision_state = tuple(tuple(row) for row in vision)  # Convertir la vision en un état immuable (tuple de tuples)

        if random() < self.exploration:
            self.exploration *= 0.999
            return choice(ACTIONS)
        else:
            return self.qtable.best_action(vision_state)

    def __repr__(self):
        return f"{self.position} score:{self.score} exploration:{self.exploration}"

class PelletManager:
    def __init__(self, maze):
        self.original_maze = maze
        self.reset_pellets()

    def reset_pellets(self):
        """Initialise ou réinitialise la liste des pellets à collecter."""
        self.pellets = {
            position for position, tile in self.original_maze.items()
            if tile in [TILE_PELLET, TILE_POWER_PELLET]
        }

    def collect_pellet(self, position):
        """Supprime un pellet de la liste si collecté."""
        if position in self.pellets:
            self.pellets.remove(position)

    def are_all_pellets_collected(self):
        """Vérifie si tous les pellets ont été collectés."""
        return len(self.pellets) == 0


class Environment:
    def __init__(self, text, start=(1, 1), ghost_start=(7, 7)):
        rows = text.strip().split('\n')
        self.height = len(rows)
        self.width = len(rows[0])
        self.maze = {}
        self.pellet_manager = PelletManager(self.maze)
        self.start = start
        self.ghost_start = ghost_start
        self.ghost_position = ghost_start
        for i in range(len(rows)):
            for j in range(len(rows[i])):
                self.maze[(i, j)] = rows[i][j]

    def reset_maze(self):
        rows = MAZE.strip().split('\n')
        for i in range(len(rows)):
            for j in range(len(rows[i])):
                self.maze[(i, j)] = rows[i][j]
        self.pellet_manager.reset_pellets()
        self.ghost_position = self.ghost_start

    import collections

    def move_ghost(self, pacman_position):
        def manhattan_distance(pos1, pos2):
            return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

        def bfs(start, goal):
            queue = collections.deque([[start]])
            seen = set([start])
            while queue:
                path = queue.popleft()
                x, y = path[-1]
                if (x, y) == goal:
                    return path
                for move in MOVES.values():
                    next_pos = (x + move[0], y + move[1])
                    if next_pos in self.maze and self.maze[next_pos] != TILE_WALL and next_pos not in seen:
                        queue.append(path + [next_pos])
                        seen.add(next_pos)
            return []

        path = bfs(self.ghost_position, pacman_position)
        if len(path) > 1:
            self.ghost_position = path[1]

    def are_all_pellets_collected(self):
        return all(tile not in [TILE_PELLET, TILE_POWER_PELLET] for tile in self.maze.values())

    def move(self, position, action):
        move = MOVES[action]
        new_position = (position[0] + move[0], position[1] + move[1])

        # Debug
        # print(f"Agent moving from {position} to {new_position}")
        # print(f"Ghost is at {self.ghost_position}")

        if new_position not in self.maze:
            reward = REWARD_OUT
        elif self.maze[new_position] in [TILE_WALL]:
            reward = REWARD_WALL
        elif self.maze[new_position] in [TILE_PELLET, TILE_POWER_PELLET]:
            reward = REWARD_PELLET
            position = new_position
            self.maze[new_position] = ' '
            self.pellet_manager.collect_pellet(position)
            if self.pellet_manager.are_all_pellets_collected():
                reward += REWARD_WIN
        elif new_position == self.ghost_position:
            print(f"Collision detected: Agent at {new_position}, Ghost at {self.ghost_position}")
            reward = REWARD_GHOST
            position = self.start  # Reset agent's position
        else:
            reward = REWARD_DEFAULT
            position = new_position

        return position, reward

    def get_vision(self, position, vision_size=3):
        """
        Retourne une vision locale autour de l'agent.
        vision_size : La taille de la fenêtre carrée (3x3, 5x5, etc.).
        """
        radius = vision_size // 2
        vision = []

        for i in range(-radius, radius + 1):
            row = []
            for j in range(-radius, radius + 1):
                pos = (position[0] + i, position[1] + j)
                row.append(self.maze.get(pos, 'x'))  # 'x' par défaut pour les limites du labyrinthe
            vision.append(row)

        return vision

class MazeWindow(arcade.Window):
    def __init__(self, agent):
        super().__init__(SPRITE_SIZE * env.width, SPRITE_SIZE * env.height, "Pacman AI")
        self.agent = agent
        self.env = agent.env
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        self.walls = arcade.SpriteList()
        self.pellets = arcade.SpriteList()
        for state in env.maze:
            if env.maze[state] is TILE_WALL: # Walls
                sprite = self.create_sprite('assets/wall.png', state)
                self.walls.append(sprite)
            elif env.maze[state] is TILE_PELLET: # Pellets
                sprite = self.create_sprite('assets/pellet.png', state)
                self.pellets.append(sprite)
            elif env.maze[state] is TILE_POWER_PELLET: # Power Pellets
                sprite = self.create_sprite('assets/power_pellet.png', state)
                self.pellets.append(sprite)

        self.player = self.create_sprite('assets/pacman.png', agent.position)
        self.ghost = self.create_sprite('assets/ghost.png', self.env.ghost_position)

    def create_sprite(self, resource, state):
        sprite = arcade.Sprite(resource, 0.5)
        sprite.center_x, sprite.center_y = (state[1] + 0.5) * SPRITE_SIZE, (env.height - state[0] - 0.5) * SPRITE_SIZE
        return sprite

    def on_draw(self):
        arcade.start_render()
        self.walls.draw()
        self.pellets.draw()
        self.player.draw()
        self.ghost.draw()
        arcade.draw_text(f'{self.agent}', 10, 10, arcade.csscolor.WHITE, 20)

    def on_update(self, delta_time):
        if not self.env.pellet_manager.are_all_pellets_collected():
            self.agent.do()
            self.player.center_x, self.player.center_y = \
                (self.agent.position[1] + 0.5) * SPRITE_SIZE, \
                (env.height - self.agent.position[0] - 0.5) * SPRITE_SIZE

            for pellet in self.pellets:
                if (pellet.center_x, pellet.center_y) == \
                        ((self.agent.position[1] + 0.5) * SPRITE_SIZE,
                         (env.height - self.agent.position[0] - 0.5) * SPRITE_SIZE):
                    self.pellets.remove(pellet)
                    break

            self.env.move_ghost(self.agent.position)
            self.ghost.center_x, self.ghost.center_y = \
                (self.env.ghost_position[1] + 0.5) * SPRITE_SIZE, \
                (env.height - self.env.ghost_position[0] - 0.5) * SPRITE_SIZE

            if self.agent.position == self.env.ghost_position:
                print("Collision avec un fantôme ! Partie perdue.")
                self.agent.reset()
                self.setup()
        else:
            # Tous les pellets sont collectés
            print("Tous les pellets ont été collectés !")
            self.agent.reset()
            self.setup()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.agent.reset()
            self.setup()
        elif key == arcade.key.E:
            self.agent.shake()


if __name__ == "__main__":
    env = Environment(MAZE, start=(1, 1))
    print(env.start)

    agent = Agent(env)
    if os.path.exists(FILE_AGENT):
        agent.load(FILE_AGENT)
    print(agent)

    window = MazeWindow(agent)
    window.setup()
    arcade.run()

    agent.save(FILE_AGENT)

    plt.plot(agent.history)
    plt.show()

    exit(0)
    # print(env.goal)
    # for i in range(50):
    #     agent.reset()
    #     iteration = 1
    #     while agent.position != env.goal and iteration < 1000:
    #         # print(f"#{iteration} {agent.position}")
    #         action, reward = agent.do()
    #         # print(f"{action} -> {agent.position} {reward}$")
    #         iteration += 1
    #     print(iteration)
    # print(agent.qtable)
