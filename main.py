import os.path
from random import choice
import arcade
import pickle

MAZE = """
xxxxxxxxxxxxxxxxxxxxxxxx
x..........xx..........x
x.xxx.xxxx.xx.xxxx.xxx.x
x.xxx.xxxx.xx.xxxx.xxx.x
x.xxx.xxxx.xx.xxxx.xxx.x
x.xxx.xxxx.xx.xxxx.xxx.x
x...?..................x
x.xxx.x.xxxxxxx.xx.xxx.x
x.xxx.x....xx...xx.xxx.x
x.xxx.xxxx.xx.xxxx.xxx.x
x.xxx..............xxx!x
xxxxxxxxxxxxxxxxxxxxxxxx
"""

TILE_WALL = 'x'

ACTION_UP = 'U'
ACTION_DOWN = 'D'
ACTION_LEFT = 'L'
ACTION_RIGHT = 'R'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT]
REWARD_OUT = -100
REWARD_WALL = -100
REWARD_GOAL = 1000
REWARD_DEFAULT = -1

SPRITE_SIZE = 64

MOVES = {ACTION_UP: (-1, 0),
         ACTION_DOWN: (1, 0),
         ACTION_LEFT: (0, -1),
         ACTION_RIGHT: (0, 1)}


def arg_max(table):
    return max(table, key=table.get)


class QTable:
    def __init__(self, learning_rate=1, discount_factor=0.5):
        self.dic = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def set(self, state, action, reward, new_state):
        if state not in self.dic:
            self.dic[state] = {ACTION_UP: 0, ACTION_DOWN: 0, ACTION_LEFT: 0, ACTION_RIGHT: 0}
        if new_state not in self.dic:
            self.dic[new_state] = {ACTION_UP: 0, ACTION_DOWN: 0, ACTION_LEFT: 0, ACTION_RIGHT: 0}

        self.dic[state][action] += reward

        delta = reward + self.discount_factor * max(self.dic[new_state].values()) - self.dic[state][action]
        self.dic[state][action] += self.learning_rate * delta
        # Q(s, a) = Q(s, a) + alpha * [reward + gamma * max(S', a) - Q(s, a)]

    def best_action(self, position):
        if position in self.dic:
            return arg_max(self.dic[position])
        else:
            return choice(ACTIONS)

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump(self.dic, file)

    def load(self, filename):
        with open(filename, 'rb') as file:
            self.dic = pickle.load(file)

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
        self.reset()
        self.qtable = QTable()

    def reset(self):
        self.position = env.start
        self.score = 0

    def do(self, action=None):
        if not action:
            action = self.best_action()

        new_position, reward = self.env.move(self.position, action)
        self.qtable.set(self.position, action, reward, new_position)
        self.position = new_position
        self.score += reward

        return action, reward

    def best_action(self):
        return self.qtable.best_action(self.position)

    def __repr__(self):
        return f"{self.position} score:{self.score}"


class Environment:
    def __init__(self, text):
        rows = text.strip().split('\n')
        self.height = len(rows)
        self.width = len(rows[0])
        self.maze = {}
        for i in range(len(rows)):
            for j in range(len(rows[i])):
                self.maze[(i, j)] = rows[i][j]
                if rows[i][j] == '?':
                    self.start = (i, j)
                elif rows[i][j] == '!':
                    self.goal = (i, j)

    def move(self, position, action):
        move = MOVES[action]
        new_position = (position[0] + move[0], position[1] + move[1])

        if new_position not in self.maze:
            reward = REWARD_OUT
        elif self.maze[new_position] in [TILE_WALL]:
            reward = REWARD_WALL
        elif self.maze[new_position] == '!':
            reward = REWARD_GOAL
            position = new_position
        else:
            reward = REWARD_DEFAULT
            position = new_position

        return position, reward


class MazeWindow(arcade.Window):
    def __init__(self, agent):
        super().__init__(SPRITE_SIZE * env.width, SPRITE_SIZE * env.height, "ESGI Maze")
        self.agent = agent
        self.env = agent.env
        arcade.set_background_color(arcade.color.BLACK)

    def setup(self):
        self.walls = arcade.SpriteList()
        for state in env.maze:
            if env.maze[state] is TILE_WALL:
                sprite = self.create_sprite(':resources:images/tiles/brickGrey.png', state)
                self.walls.append(sprite)

        self.goal = self.create_sprite(':resources:images/items/flagGreen1.png', env.goal)
        self.player = self.create_sprite(':resources:images/enemies/mouse.png', agent.position)

    def create_sprite(self, resource, state):
        sprite = arcade.Sprite(resource, 0.5)
        sprite.center_x, sprite.center_y = (state[1] + 0.5) * SPRITE_SIZE, (env.height - state[0] - 0.5) * SPRITE_SIZE
        return sprite

    def on_draw(self):
        arcade.start_render()
        self.walls.draw()
        self.goal.draw()
        self.player.draw()
        arcade.draw_text(f'{self.agent.score}', 10, 10, arcade.csscolor.WHITE, 20)

    def on_update(self, delta_time):
        if self.agent.position != self.env.goal:
            self.agent.do()
            self.player.center_x, self.player.center_y = \
                (self.agent.position[1] + 0.5) * SPRITE_SIZE, \
                (env.height - self.agent.position[0] - 0.5) * SPRITE_SIZE

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            self.agent.reset()
        elif key == arcade.key.T:
            self.env.maze[(4, 5)] = TILE_WALL
            self.setup()


if __name__ == "__main__":
    env = Environment(MAZE)
    print(env.start)

    agent = Agent(env)
    if os.path.exists('mouse.qtable'):
        agent.qtable.load('mouse.qtable')
    print(agent)

    window = MazeWindow(agent)
    window.setup()
    arcade.run()

    agent.qtable.save('mouse.qtable')

    exit(0)

    print(env.goal)
    for i in range(50):
        agent.reset()
        iteration = 1
        while agent.position != env.goal and iteration < 1000:
            # print(f"#{iteration} {agent.position}")
            action, reward = agent.do()
            # print(f"{action} -> {agent.position} {reward}$")
            iteration += 1
        print(iteration)
    print(agent.qtable)







#
# import arcade
# import random
#
# # Définition des constantes
# SCREEN_WIDTH = 600
# SCREEN_HEIGHT = 600
# SCREEN_TITLE = "Génération Aléatoire de Carte Pacman"
#
# TILE_SIZE = 20
# ROWS = SCREEN_HEIGHT // TILE_SIZE
# COLUMNS = SCREEN_WIDTH // TILE_SIZE
#
# # Nombre de fantômes
# NUM_GHOSTS = 4
#
# class MazeGenerator:
#     def __init__(self, rows, columns):
#         self.rows = rows
#         self.columns = columns
#         # Initialiser la grille avec des murs partout
#         self.grid = [[1 for _ in range(columns)] for _ in range(rows)]
#
#     def generate_maze(self):
#         # Commencer à la position (1, 1)
#         self._carve_passages_from(1, 1)
#
#     def _carve_passages_from(self, cx, cy):
#         directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
#         random.shuffle(directions)
#         for dx, dy in directions:
#             nx, ny = cx + dx, cy + dy
#             if 1 <= nx < self.columns - 1 and 1 <= ny < self.rows - 1:
#                 if self.grid[ny][nx] == 1:
#                     self.grid[ny][nx] = 0
#                     self.grid[cy + dy // 2][cx + dx // 2] = 0
#                     self._carve_passages_from(nx, ny)
#
# class PacmanMap(arcade.Window):
#     def __init__(self):
#         super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
#         arcade.set_background_color(arcade.color.BLACK)
#         self.maze = MazeGenerator(ROWS, COLUMNS)
#         self.wall_list = None
#         self.player_sprite = None
#         self.ghost_sprites = None
#
#     def setup(self):
#         self.maze.generate_maze()
#         self.wall_list = arcade.SpriteList()
#         # Créer les murs en fonction de la grille générée
#         for row in range(self.maze.rows):
#             for column in range(self.maze.columns):
#                 if self.maze.grid[row][column] == 1:
#                     x = column * TILE_SIZE + TILE_SIZE // 2
#                     y = row * TILE_SIZE + TILE_SIZE // 2
#                     wall = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.BLUE)
#                     wall.center_x = x
#                     wall.center_y = y
#                     self.wall_list.append(wall)
#
#         # Créer le sprite du joueur
#         self.player_sprite = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.YELLOW)
#         # Trouver une position de départ pour le joueur (case vide)
#         self.player_sprite.center_x, self.player_sprite.center_y = self.get_random_empty_cell()
#
#         # Créer les sprites des fantômes
#         self.ghost_sprites = arcade.SpriteList()
#         for _ in range(NUM_GHOSTS):
#             ghost = arcade.SpriteSolidColor(TILE_SIZE, TILE_SIZE, arcade.color.RED)
#             ghost.center_x, ghost.center_y = self.get_random_empty_cell()
#             self.ghost_sprites.append(ghost)
#
#     def get_random_empty_cell(self):
#         # Trouver une position vide dans le labyrinthe
#         while True:
#             row = random.randint(1, self.maze.rows - 2)
#             column = random.randint(1, self.maze.columns - 2)
#             if self.maze.grid[row][column] == 0:
#                 x = column * TILE_SIZE + TILE_SIZE // 2
#                 y = row * TILE_SIZE + TILE_SIZE // 2
#                 return x, y
#
#     def on_draw(self):
#         arcade.start_render()
#         self.wall_list.draw()
#         self.player_sprite.draw()
#         self.ghost_sprites.draw()
#
#     def on_key_press(self, key, modifiers):
#         if key == arcade.key.I:
#             # Regénérer le labyrinthe
#             self.maze = MazeGenerator(ROWS, COLUMNS)
#             self.setup()
#
# def main():
#     window = PacmanMap()
#     window.setup()
#     arcade.run()
#
# if __name__ == "__main__":
#     main()
#
#
# xxxxxxxxxxxxxxxxxxxxxxx
# x?...........x........x
# x.xxxx.xxxxx.xxxx.xxx.x
# x..x..x.x...xxx..x.x.xx
# x.x..x.x...x.xx...x.x.x
# x.xxxx.xxxxx.xxxx.xxx.x
# x.....................x
# x.xxxx.xx.xxxxxxx.xxx.x
# x.x  x.xx....xx.....x.x
# x.x  x.xxxxx.xx.xxx.x.x
# x.xxxx............xx..x
# x........xxxxxxxxx...!x
# xxxxxxxxxxxxxxxxxxxxxxx
