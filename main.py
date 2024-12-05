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
TILE_COIN = '.'
TILE_POWER_PELLET = 'o'
TILE_GHOST = 'G'

NUMBER_OF_COINS = 78

ACTION_UP = 'U'
ACTION_DOWN = 'D'
ACTION_LEFT = 'L'
ACTION_RIGHT = 'R'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT]
REWARD_OUT = -50
REWARD_WALL = -20
REWARD_COIN = 20
REWARD_ALL_COINS_COLLECTED = 500
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
        # Utiliser des tuples immuables pour les états
        if state not in self.dic:
            self.dic[state] = {ACTION_UP: 0, ACTION_DOWN: 0, ACTION_LEFT: 0, ACTION_RIGHT: 0}
        if new_state not in self.dic:
            self.dic[new_state] = {ACTION_UP: 0, ACTION_DOWN: 0, ACTION_LEFT: 0, ACTION_RIGHT: 0}

        delta = reward + self.discount_factor * max(self.dic[new_state].values()) - self.dic[state][action]
        self.dic[state][action] += self.learning_rate * delta

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
        self.env.reset_ghost() # Réinitialisation de la position du fantôme
        self.position = self.env.start
        self.score = 0
        self.earned_coins = 0
        self.is_game_over = False  # Réinitialisation de l'état de jeu

    def do(self, action=None):
        if not action:
            action = self.best_action()

        # Ajouter la vision au state (sans inclure la position de l'agent)
        vision = tuple(sorted(self.env.get_vision(self.position).items()))  # Convertir en tuple trié
        current_state = (self.env.ghost_position, vision)

        new_position, reward = self.env.move(self.position, action)
        vision = tuple(sorted(self.env.get_vision(new_position).items()))  # Mettre à jour la vision
        new_state = (self.env.ghost_position, vision)

        if new_position == self.env.ghost_position:
            reward += REWARD_GAME_OVER
            self.score += REWARD_GAME_OVER
            self.is_game_over = True
            return action, reward

        # Mettre à jour la Q-table
        self.qtable.set(current_state, action, reward, new_state)
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
        vision = tuple(sorted(self.env.get_vision(self.position).items()))
        state = (self.env.ghost_position, vision)  # Exclure la position de l'agent
        return self.qtable.best_action(state)

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

    def get_vision(self, position):
        vision = {}
        for action, move in MOVES.items():
            neighbor = (position[0] + move[0], position[1] + move[1])
            if neighbor in self.maze:
                vision[action] = self.maze[neighbor]
            else:
                vision[action] = TILE_WALL  # Considérer les cases hors de la grille comme des murs
        return vision

    def move_ghost(self, agent_position):
        """Déplace le fantôme en direction de l'agent."""
        ghost_row, ghost_col = self.ghost_position
        agent_row, agent_col = agent_position  # Utilisez la position de l'agent passée en paramètre

        # Calculez les déplacements possibles
        possible_moves = []
        for action, move in MOVES.items():
            new_position = (ghost_row + move[0], ghost_col + move[1])
            if new_position in self.maze and self.maze[new_position] != TILE_WALL:
                possible_moves.append((new_position, action))

        if not possible_moves:
            return  # Si aucune direction n'est possible, ne bouge pas

        # Choisissez le mouvement qui rapproche le plus le fantôme de l'agent
        def distance_to_agent(pos):
            return abs(pos[0] - agent_row) + abs(pos[1] - agent_col)

        # Classez les mouvements par distance à l'agent
        possible_moves.sort(key=lambda x: distance_to_agent(x[0]))

        # Petite probabilité d'aléatoire pour l'imprévisibilité
        if len(possible_moves) > 1 and choice([True, False]):  # 50% de chance d'aléatoire
            _, action = choice(possible_moves)
        else:
            _, action = possible_moves[0]  # Choisissez le mouvement optimal

        # Appliquez le déplacement choisi
        move = MOVES[action]
        self.ghost_position = (ghost_row + move[0], ghost_col + move[1])

    def reset_ghost(self):
        """Réinitialise la position du fantôme à sa position initiale."""
        self.ghost_position = next((pos for pos, tile in self.initial_maze.items() if tile == TILE_GHOST), None)


    def reset_maze(self):
        """Réinitialise le labyrinthe à son état initial."""
        self.maze = self.initial_maze.copy()

    def move(self, position, action):
        move = MOVES[action]
        new_position = (position[0] + move[0], position[1] + move[1])

        if new_position not in self.maze or self.maze[new_position] == TILE_WALL:
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
            self.env.move_ghost(self.agent.position)

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
                print(f"Partie terminée perdu ! Score final : {self.agent.score}")
                self.agent.reset()
                self.reset_sprites()
        else:
            # Partie terminée ou tous les coins collectés
            print(f"Partie terminée gagné ! Score final : {self.agent.score}")
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