import os.path
from random import choice
import arcade
import pickle
import matplotlib.pyplot as plt

MAZE = """
###############
#o..?#...#...o#
#.##.#.#.#.##.#
#.#.........#.#
#.#.##.#.##.#.#
#......#......#
#.#.##.#.##.#.#
#.#.........#G#
#.##.#.#.#.##.#
#o...#...#...o#
###############
"""

TILE_WALL = '#'
TILE_VOID = '@'
TILE_COIN = '.'
TILE_POWER_PELLET = 'o'
TILE_GHOST = 'G'

NUMBER_OF_COINS = 78

ACTION_UP = 'U'
ACTION_DOWN = 'D'
ACTION_LEFT = 'L'
ACTION_RIGHT = 'R'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT]
REWARD_OUT = -100
REWARD_WALL = -100
REWARD_COIN = 10
REWARD_ALL_COINS_COLLECTED = 1000
REWARD_GAME_OVER = -1000  # Malus pour avoir touché un fantôme

REWARD_DEFAULT = -1

SPRITE_SIZE = 64

MOVES = {ACTION_UP: (-1, 0),
         ACTION_DOWN: (1, 0),
         ACTION_LEFT: (0, -1),
         ACTION_RIGHT: (0, 1)}


def arg_max(table):
    return max(table, key=table.get)


class QTable:
    def __init__(self, learning_rate=1, discount_factor=0.8):
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
        self.score_history = []
        self.score = None
        self.reset()
        self.qtable = QTable()
        self.is_game_over = False  # Nouvel attribut pour vérifier si la partie est terminée

    def reset(self):
        if self.score:
            self.score_history.append(self.score)
        self.env.reset_maze()
        self.position = self.env.start
        self.score = 0
        self.earned_coins = 0
        self.is_game_over = False  # Réinitialisation de l'état de jeu

    def do(self, action=None):
        if not action:
            action = self.best_action()

        new_position, reward = self.env.move(self.position, action)

        # Vérifiez si l'agent touche le fantôme
        if new_position == self.env.ghost_position:
            reward += REWARD_GAME_OVER
            self.score += REWARD_GAME_OVER
            self.is_game_over = True  # Marquez la partie comme terminée
            return action, reward

        # Mettez à jour la position et récompense
        self.qtable.set(self.position, action, reward, new_position)
        self.position = new_position
        self.score += reward

        if self.env.maze[new_position] in (TILE_COIN, TILE_POWER_PELLET):
            self.earned_coins += 1
            self.env.maze[new_position] = ' '

        if self.earned_coins == NUMBER_OF_COINS:
            reward += REWARD_ALL_COINS_COLLECTED
            self.score += REWARD_ALL_COINS_COLLECTED

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
        self.initial_maze = {}
        self.ghost_position = None  # Position initiale du fantôme

        for i in range(len(rows)):
            for j in range(len(rows[i])):
                self.maze[(i, j)] = rows[i][j]
                self.initial_maze[(i, j)] = rows[i][j]
                if rows[i][j] == '?':
                    self.start = (i, j)
                elif rows[i][j] == '.':
                    self.coin = (i, j)
                elif rows[i][j] == TILE_GHOST:
                    self.ghost_position = (i, j)  # Initialisation du fantôme

    def move_ghost(self):
        """Déplace le fantôme dans une direction aléatoire."""
        action = choice(ACTIONS)
        move = MOVES[action]
        new_position = (self.ghost_position[0] + move[0], self.ghost_position[1] + move[1])

        # Vérifiez que le fantôme reste dans le labyrinthe et n'entre pas dans des murs ou des voids.
        if new_position in self.maze and self.maze[new_position] not in [TILE_WALL, TILE_VOID]:
            self.ghost_position = new_position

    def reset_maze(self):
        """Réinitialise le labyrinthe à son état initial."""
        self.maze = self.initial_maze.copy()

    def move(self, position, action):
        move = MOVES[action]
        new_position = (position[0] + move[0], position[1] + move[1])

        if new_position not in self.maze or self.maze[new_position] in [TILE_VOID]:
            reward = REWARD_OUT
        elif self.maze[new_position] in [TILE_WALL]:
            reward = REWARD_WALL
        elif self.maze[new_position] == '.':
            reward = REWARD_COIN
            position = new_position
        elif self.maze[new_position] == 'o':
            reward = REWARD_COIN
            position = new_position
        else:
            reward = REWARD_DEFAULT
            position = new_position

        return position, reward


class MazeWindow(arcade.Window):

    def __init__(self, agent, fast_mode=False):
        super().__init__(SPRITE_SIZE * env.width, SPRITE_SIZE * env.height, "AI Pacman le golmon")
        self.agent = agent
        self.env = agent.env
        self.fast_mode = fast_mode  # Ajoutez un mode rapide
        arcade.set_background_color(arcade.color.BLACK)

    def create_sprite(self, resource, state):
        sprite = arcade.Sprite(resource, 0.5)
        sprite.center_x, sprite.center_y = (state[1] + 0.5) * SPRITE_SIZE, (
                    self.env.height - state[0] - 0.5) * SPRITE_SIZE
        return sprite

    def setup(self):
        self.walls = arcade.SpriteList()
        self.coins = arcade.SpriteList()
        self.coin_sprites = {}
        for state in env.maze:
            if env.maze[state] is TILE_WALL:
                sprite = self.create_sprite('assets/wall.png', state)
                self.walls.append(sprite)

            if env.maze[state] is TILE_COIN:
                coin = self.create_sprite('assets/pellet.png', state)
                self.coins.append(coin)
                self.coin_sprites[state] = coin

            if env.maze[state] is TILE_POWER_PELLET:
                pellet = self.create_sprite('assets/power_pellet.png', state)
                self.coins.append(pellet)
                self.coin_sprites[state] = pellet

        self.player = self.create_sprite('assets/pacman.png', agent.position)

        self.ghost = self.create_sprite('assets/ghost_1.png',self.env.ghost_position)

    def reset_sprites(self):
        self.coins = arcade.SpriteList()
        self.coin_sprites = {}
        for state in self.env.maze:
            if self.env.maze[state] == TILE_COIN:
                coin = self.create_sprite('assets/pellet.png', state)
                self.coins.append(coin)
                self.coin_sprites[state] = coin

            if self.env.maze[state] == TILE_POWER_PELLET:
                pellet = self.create_sprite('assets/power_pellet.png', state)
                self.coins.append(pellet)
                self.coin_sprites[state] = pellet

    def on_draw(self):
        arcade.start_render()
        self.walls.draw()
        self.coins.draw()
        self.player.draw()
        self.ghost.draw()
        arcade.draw_text(f'Score: {self.agent.score}, Coins:{self.agent.earned_coins}', 10, 10, arcade.csscolor.WHITE,
                         20)

        # Affichez "Game Over" si la partie est terminée
        if self.agent.is_game_over:
            arcade.draw_text("GAME OVER", self.width // 2, self.height // 2,
                             arcade.color.RED, 50, anchor_x="center")

    def on_update(self, delta_time):
        if not self.agent.is_game_over and self.agent.earned_coins < NUMBER_OF_COINS:
            previous_position = self.agent.position
            self.agent.do()
            new_position = self.agent.position

            # Déplacez le fantôme
            self.env.move_ghost()

            # Mise à jour de la position du joueur
            self.player.center_x, self.player.center_y = \
                (new_position[1] + 0.5) * SPRITE_SIZE, \
                (env.height - new_position[0] - 0.5) * SPRITE_SIZE

            # Mise à jour de la position du fantôme
            self.ghost.center_x, self.ghost.center_y = \
                (self.env.ghost_position[1] + 0.5) * SPRITE_SIZE, \
                (env.height - self.env.ghost_position[0] - 0.5) * SPRITE_SIZE

            # Vérifiez si une pièce a été collectée
            if previous_position != new_position and new_position in self.coin_sprites:
                coin_sprite = self.coin_sprites[new_position]
                self.coins.remove(coin_sprite)
                del self.coin_sprites[new_position]

            # Vérifiez si le jeu est terminé (collision avec le fantôme)
            if self.agent.is_game_over:
                print(f"Partie terminée ! Score final : {self.agent.score}")
                self.agent.reset()
                self.reset_sprites()
        else:
            # Partie terminée ou tous les coins collectés
            print(f"Partie terminée ! Score final : {self.agent.score}")
            self.agent.reset()
            self.reset_sprites()


if __name__ == "__main__":
    env = Environment(MAZE)
    print(env.start)

    agent = Agent(env)
    if os.path.exists('mouse.qtable'):
        agent.qtable.load('mouse.qtable')
    print(agent)

    window = MazeWindow(agent, False)
    window.setup()
    arcade.run()

    agent.qtable.save('mouse.qtable')

    plt.plot(agent.score_history)
    plt.show()

    exit(0)