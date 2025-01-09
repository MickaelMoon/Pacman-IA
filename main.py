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
REWARD_WALL = -300
REWARD_REPEAT = 0          # <-- NOUVEAU malus quand on revisite une case
REWARD_WIN = 1000
REWARD_PELLET = 10
REWARD_DEFAULT = -1
REWARD_GHOST = -10000

WIN = 1
LOOSE = 0

SPRITE_SIZE = 64

MOVES = {
    ACTION_UP: (-1, 0),
    ACTION_DOWN: (1, 0),
    ACTION_LEFT: (0, -1),
    ACTION_RIGHT: (0, 1)
}


def arg_max(table):
    return max(table, key=table.get)


class QTable:
    def __init__(self, learning_rate=0.9, discount_factor=0.5):
        self.dic = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def set(self, state, action, reward, new_state):
        if state not in self.dic:
            self.dic[state] = {a: 0 for a in ACTIONS}
        if new_state not in self.dic:
            self.dic[new_state] = {a: 0 for a in ACTIONS}

        delta = (
            reward
            + self.discount_factor * max(self.dic[new_state].values())
            - self.dic[state][action]
        )
        self.dic[state][action] += self.learning_rate * delta

    def best_action(self, position):
        if position in self.dic:
            return arg_max(self.dic[position])
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


class Agent:
    def __init__(self, env):
        self.env = env
        self.history = []
        self.score = None
        self.qtable = QTable()
        self.exploration = 0
        self.reset()

    def reset(self):
        if self.score is not None:
            self.history.append(self.score)
        self.position = self.env.start
        self.score = 0
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
        # État (vision)
        current_vision = self.env.get_vision(self.position)
        current_state = tuple(tuple(row) for row in current_vision)

        # Choix de l'action
        if action is None:
            action = self.best_action()
        
        # Action -> nouvel état
        new_position, reward = self.env.move(self.position, action)

        # Nouvelle vision
        new_vision = self.env.get_vision(new_position)
        new_state = tuple(tuple(row) for row in new_vision)

        # Mise à jour de la Q-table
        self.qtable.set(current_state, action, reward, new_state)

        # Mise à jour de l'agent
        self.position = new_position
        self.score += reward
        print("action, reward =", action, reward)
        return action, reward

    def best_action(self):
        vision = self.env.get_vision(self.position)
        vision_state = tuple(tuple(row) for row in vision)

        # Ici, tu as désactivé l'exploration. L'agent prend toujours la meilleure action connue.
        # (On laisse self.exploration à 0, ou on la met à un autre usage ?)
        # S'il n'y a pas de table connue, on fait un choix aléatoire.
        return self.qtable.best_action(vision_state)

    def __repr__(self):
        return f"{self.position} score:{self.score:.1f} exploration:{self.exploration}"


class PelletManager:
    def __init__(self, maze):
        self.original_maze = maze
        self.reset_pellets()

    def reset_pellets(self):
        self.pellets = {
            position
            for position, tile in self.original_maze.items()
            if tile in [TILE_PELLET, TILE_POWER_PELLET]
        }

    def collect_pellet(self, position):
        if position in self.pellets:
            self.pellets.remove(position)

    def are_all_pellets_collected(self):
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

        # Ensemble des cases déjà visitées (pour le malus "repeat")
        self.visited_positions = set()

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

        # Réinitialise l'historique des positions visitées
        self.visited_positions = set()

    def move_ghost(self, pacman_position):
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
                    if (next_pos in self.maze
                            and self.maze[next_pos] != TILE_WALL
                            and next_pos not in seen):
                        queue.append(path + [next_pos])
                        seen.add(next_pos)
            return []

        path = bfs(self.ghost_position, pacman_position)
        if len(path) > 1:
            self.ghost_position = path[1]

    def are_all_pellets_collected(self):
        return all(tile not in [TILE_PELLET, TILE_POWER_PELLET]
                   for tile in self.maze.values())

    def move(self, position, action):
        move = MOVES[action]
        new_position = (position[0] + move[0], position[1] + move[1])

        reward = 0

        # Vérifier la validité du déplacement
        if new_position not in self.maze:
            reward += REWARD_OUT
        elif self.maze[new_position] == TILE_WALL:
            reward += REWARD_WALL
        elif self.maze[new_position] in [TILE_PELLET, TILE_POWER_PELLET]:
            reward += REWARD_PELLET
            position = new_position
            self.maze[new_position] = ' '  # On enlève le pellet du labyrinthe
            self.pellet_manager.collect_pellet(position)

            # Si tous les pellets sont mangés, on ajoute la récompense de victoire
            if self.pellet_manager.are_all_pellets_collected():
                reward += REWARD_WIN
        elif new_position == self.ghost_position:
            # Collision fantôme
            # print(f"Collision detected: Agent at {new_position}, Ghost at {self.ghost_position}")
            reward += REWARD_GHOST
            position = self.start
        else:
            # Mouvement normal
            position = new_position

        # Vérifier si c'est une case déjà visitée (et non la case de départ forcé après un reset)
        if position in self.visited_positions:
            reward += REWARD_REPEAT  # Malus pour revisiter
        else:
            self.visited_positions.add(position)
            
        reward += REWARD_DEFAULT

        return position, reward

    def get_vision(self, position, vision_size=5):
        radius = vision_size // 2
        vision = []
        for i in range(-radius, radius + 1):
            row = []
            for j in range(-radius, radius + 1):
                pos = (position[0] + i, position[1] + j)
                if pos == self.ghost_position:
                    row.append('G')
                else:
                    row.append(self.maze.get(pos, 'x'))
            vision.append(row)
        return vision


class MazeWindow(arcade.Window):
    def __init__(self, agent):
        super().__init__(SPRITE_SIZE * env.width, SPRITE_SIZE * env.height, "Pacman AI")
        self.agent = agent
        self.env = agent.env
        arcade.set_background_color(arcade.color.BLACK)
        self.set_update_rate(1 / 1500)

    def setup(self):
        self.walls = arcade.SpriteList()
        self.pellets = arcade.SpriteList()

        for state in env.maze:
            if env.maze[state] == TILE_WALL:
                sprite = self.create_sprite('assets/wall.png', state)
                self.walls.append(sprite)
            elif env.maze[state] == TILE_PELLET:
                sprite = self.create_sprite('assets/pellet.png', state)
                self.pellets.append(sprite)
            elif env.maze[state] == TILE_POWER_PELLET:
                sprite = self.create_sprite('assets/power_pellet.png', state)
                self.pellets.append(sprite)

        self.player = self.create_sprite('assets/pacman.png', self.agent.position)
        self.ghost = self.create_sprite('assets/ghost.png', self.env.ghost_position)

    def create_sprite(self, resource, state):
        sprite = arcade.Sprite(resource, 0.5)
        sprite.center_x = (state[1] + 0.5) * SPRITE_SIZE
        sprite.center_y = (env.height - state[0] - 0.5) * SPRITE_SIZE
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

            # Mise à jour position graphique du pacman
            self.player.center_x = (self.agent.position[1] + 0.5) * SPRITE_SIZE
            self.player.center_y = (env.height - self.agent.position[0] - 0.5) * SPRITE_SIZE

            # Supprimer les sprites de pellets mangés
            for pellet in self.pellets:
                if (pellet.center_x, pellet.center_y) == (
                    (self.agent.position[1] + 0.5) * SPRITE_SIZE,
                    (env.height - self.agent.position[0] - 0.5) * SPRITE_SIZE
                ):
                    self.pellets.remove(pellet)
                    break

            # Déplacement du fantôme
            self.env.move_ghost(self.agent.position)
            self.ghost.center_x = (self.env.ghost_position[1] + 0.5) * SPRITE_SIZE
            self.ghost.center_y = (env.height - self.env.ghost_position[0] - 0.5) * SPRITE_SIZE

            # Si collision fantôme
            if self.agent.position == self.env.ghost_position:
                self.agent.score += REWARD_GHOST
                print("Score final:", self.agent.score)
                self.agent.reset()
                self.setup()
        else:
            # print("Tous les pellets ont été collectés !")
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
    # print("Point de départ:", env.start)

    agent = Agent(env)
    if os.path.exists(FILE_AGENT):
        agent.load(FILE_AGENT)
    # print(agent)

    window = MazeWindow(agent)
    window.setup()
    arcade.run()

    agent.save(FILE_AGENT)

    plt.plot(agent.history)
    plt.title("Score history")
    plt.xlabel("Episodes")
    plt.ylabel("Score")
    plt.show()

    exit(0)