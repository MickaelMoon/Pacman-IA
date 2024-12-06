import os.path
from random import choice
import arcade
import pickle
import matplotlib.pyplot as plt

MAZE = """
#############
#o..?#.#...o#
#.##.....##.#
#.#..#.#..#.#
#.#.##.##.#.#
#.#.##.##.#.#
#.#..#.#..#.#
#.##.....##G#
#o...#.#...o#
#############
"""

TILE_WALL = '#'
TILE_COIN = '.'
TILE_POWER_PELLET = 'o'
TILE_GHOST = 'G'

NUMBER_OF_COINS = 54

ACTION_UP = 'U'
ACTION_DOWN = 'D'
ACTION_LEFT = 'L'
ACTION_RIGHT = 'R'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT]
REWARD_OUT = -50
REWARD_WALL = -30
REWARD_COIN = 30
REWARD_ALL_COINS_COLLECTED = 5000
REWARD_GAME_OVER = -1000
REWARD_DEFAULT = -2

SPRITE_SIZE = 64

MOVES = {ACTION_UP: (-1, 0),
         ACTION_DOWN: (1, 0),
         ACTION_LEFT: (0, -1),
         ACTION_RIGHT: (0, 1)}


def arg_max(table):
    return max(table, key=table.get)


class QTable:
    def __init__(self, learning_rate=0.5, discount_factor=1):
        self.dic = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def set(self, state, action, reward, new_state):
        if state not in self.dic:
            self.dic[state] = {ACTION_UP: 0, ACTION_DOWN: 0, ACTION_LEFT: 0, ACTION_RIGHT: 0}
        if new_state not in self.dic:
            self.dic[new_state] = {ACTION_UP: 0, ACTION_DOWN: 0, ACTION_LEFT: 0, ACTION_RIGHT: 0}

        delta = reward + self.discount_factor * max(self.dic[new_state].values()) - self.dic[state][action]
        self.dic[state][action] += self.learning_rate * delta

    def best_action(self, state):
        if state in self.dic:
            return arg_max(self.dic[state])
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
        self.qtable = QTable()
        self.reset()
        self.is_game_over = False

    def reset(self):
        if hasattr(self, "score") and self.score is not None:
            self.score_history.append(self.score)
        self.env.reset_maze()
        self.env.reset_ghost()
        self.position = self.env.start
        self.score = 0
        self.earned_coins = 0
        self.is_game_over = False

    def do(self, action=None):
        if not action:
            action = self.best_action()

        # Vision actuelle et position du fantôme
        vision = tuple(sorted(self.env.get_vision(self.position).items()))
        ghost_position = self.env.ghost_position
        current_state = (vision, ghost_position)

        # Effectuer une action
        new_position, reward = self.env.move(self.position, action)

        # Nouvelle vision et état futur
        vision = tuple(sorted(self.env.get_vision(new_position).items()))
        ghost_position = self.env.ghost_position
        new_state = (vision, ghost_position)

        # Récompense si le fantôme est dans la vision
        ghost_in_sight = any(tile == TILE_GHOST for tile in dict(vision).values())
        if ghost_in_sight:
            reward += REWARD_DEFAULT - 5

        # Récompense de fin de jeu si le fantôme atteint l'agent
        if new_position == self.env.ghost_position:
            print(f"GAME OVER: Agent at {new_position}, Ghost at {self.env.ghost_position}")
            reward += REWARD_GAME_OVER
            self.score += reward
            self.is_game_over = True  # Assurez-vous que cet attribut est mis à jour
            return action, reward, True

        # Mise à jour de la QTable
        self.qtable.set(current_state, action, reward, new_state)

        # Mise à jour de la position
        self.position = new_position
        self.score += reward

        # Gérer les pièces
        if self.env.maze[new_position] in (TILE_COIN, TILE_POWER_PELLET):
            self.earned_coins += 1
            self.env.maze[new_position] = ' '

        # Vérifier si le jeu est gagné
        game_won = self.earned_coins == NUMBER_OF_COINS
        if game_won:
            reward += REWARD_ALL_COINS_COLLECTED
            self.score += reward

        return action, reward, game_won

    def best_action(self):
        vision = tuple(sorted(self.env.get_vision(self.position).items()))
        state = vision
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
        self.ghost_position = None

        for i in range(len(rows)):
            for j in range(len(rows[i])):
                self.maze[(i, j)] = rows[i][j]
                self.initial_maze[(i, j)] = rows[i][j]
                if rows[i][j] == '?':
                    self.start = (i, j)
                elif rows[i][j] == TILE_GHOST:
                    self.ghost_position = (i, j)

    def get_vision(self, position):
        vision = {}
        for action, move in MOVES.items():
            neighbor = (position[0] + move[0], position[1] + move[1])
            if neighbor in self.maze:
                if neighbor == self.ghost_position:
                    vision[action] = TILE_GHOST
                else:
                    vision[action] = self.maze[neighbor]
            else:
                vision[action] = TILE_WALL
        return vision

    def reset_ghost(self):
        self.ghost_position = next((pos for pos, tile in self.initial_maze.items() if tile == TILE_GHOST), None)

    def reset_maze(self):
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

    def move_ghost(self, agent_position):
        """Déplace le fantôme vers Pac-Man."""
        ghost_row, ghost_col = self.ghost_position
        agent_row, agent_col = agent_position

        possible_moves = []
        for action, move in MOVES.items():
            new_position = (ghost_row + move[0], ghost_col + move[1])
            if new_position in self.maze and self.maze[new_position] != TILE_WALL:
                possible_moves.append((new_position, action))

        if not possible_moves:
            return

        def distance_to_agent(pos):
            return abs(pos[0] - agent_row) + abs(pos[1] - agent_col)

        possible_moves.sort(key=lambda x: distance_to_agent(x[0]))
        _, action = possible_moves[0]
        move = MOVES[action]
        self.ghost_position = (ghost_row + move[0], ghost_col + move[1])


class MazeWindow(arcade.Window):

    def __init__(self, agent, fast_mode=False):
        super().__init__(SPRITE_SIZE * env.width, SPRITE_SIZE * env.height, "AI Pacman le golmon")
        self.agent = agent
        self.env = agent.env
        self.fast_mode = fast_mode
        arcade.set_background_color(arcade.color.BLACK)
        self.time_since_last_update = 0  # Nouvelle variable pour contrôler la vitesse

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
        self.ghost = self.create_sprite('assets/ghost_1.png', self.env.ghost_position)

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

    def draw_vision(self):
        # Vision de l'agent
        vision = self.env.get_vision(self.agent.position)
        for direction, tile in vision.items():
            move = MOVES[direction]
            visible_pos = (self.agent.position[0] + move[0], self.agent.position[1] + move[1])
            if visible_pos in self.env.maze:
                x = (visible_pos[1] + 0.5) * SPRITE_SIZE
                y = (self.env.height - visible_pos[0] - 0.5) * SPRITE_SIZE
                arcade.draw_rectangle_filled(x, y, SPRITE_SIZE, SPRITE_SIZE, arcade.color.YELLOW + (100,))

        # Dessiner des rectangles autour de Pac-Man et du fantôme
        pac_x = (self.agent.position[1] + 0.5) * SPRITE_SIZE
        pac_y = (self.env.height - self.agent.position[0] - 0.5) * SPRITE_SIZE
        ghost_x = (self.env.ghost_position[1] + 0.5) * SPRITE_SIZE
        ghost_y = (self.env.height - self.env.ghost_position[0] - 0.5) * SPRITE_SIZE

        arcade.draw_rectangle_outline(pac_x, pac_y, SPRITE_SIZE, SPRITE_SIZE, arcade.color.BLUE, 3)
        arcade.draw_rectangle_outline(ghost_x, ghost_y, SPRITE_SIZE, SPRITE_SIZE, arcade.color.RED, 3)

    def on_draw(self):
        arcade.start_render()
        self.walls.draw()
        self.coins.draw()
        self.player.draw()
        self.ghost.draw()
        self.draw_vision()
        arcade.draw_text(f'Score: {self.agent.score}, Coins: {self.agent.earned_coins}',
                         10, 10, arcade.csscolor.WHITE, 20)

        # Afficher les informations de debug à l'écran
        debug_text = f"Agent: {self.agent.position}, Ghost: {self.env.ghost_position}"
        arcade.draw_text(debug_text, 10, 40, arcade.csscolor.RED, 16)
        if self.agent.is_game_over:
            arcade.draw_text("GAME OVER", self.width // 2, self.height // 2,
                             arcade.color.RED, 50, anchor_x="center")

    def on_update(self, delta_time):
        self.time_since_last_update += delta_time
        UPDATE_RATE = 0.02  # Temps en secondes entre chaque mise à jour (par exemple, 0.2s)

        if self.time_since_last_update >= UPDATE_RATE:
            self.time_since_last_update = 0  # Réinitialiser le compteur

            if not self.agent.is_game_over and self.agent.earned_coins < NUMBER_OF_COINS:
                previous_position = self.agent.position
                self.agent.do()
                new_position = self.agent.position
                self.env.move_ghost(self.agent.position)

                # Mettre à jour les positions des sprites
                self.player.center_x, self.player.center_y = \
                    (new_position[1] + 0.5) * SPRITE_SIZE, \
                    (env.height - new_position[0] - 0.5) * SPRITE_SIZE
                self.ghost.center_x, self.ghost.center_y = \
                    (self.env.ghost_position[1] + 0.5) * SPRITE_SIZE, \
                    (env.height - self.env.ghost_position[0] - 0.5) * SPRITE_SIZE

                # Gérer les sprites des pièces collectées
                if previous_position != new_position and new_position in self.coin_sprites:
                    coin_sprite = self.coin_sprites[new_position]
                    self.coins.remove(coin_sprite)
                    del self.coin_sprites[new_position]

                # Vérifier la fin de jeu
                if self.agent.is_game_over:
                    print(f"Partie terminée perdu ! Score final : {self.agent.score}")
                    self.agent.reset()
                    self.reset_sprites()
            else:
                print(f"Partie terminée GAGNE ! Score final : {self.agent.score}")
                self.agent.reset()
                self.reset_sprites()


if __name__ == "__main__":
    env = Environment(MAZE)
    agent = Agent(env)
    if os.path.exists('mouse.qtable'):
        agent.qtable.load('mouse.qtable')
    window = MazeWindow(agent, False)
    window.setup()
    arcade.run()
    agent.qtable.save('mouse.qtable')
    plt.plot(agent.score_history)
    plt.show()
    exit(0)
