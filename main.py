# import arcade
# import random
# import pickle
#
# # Dimensions de la fenêtre et du labyrinthe
# SCREEN_WIDTH = 900
# SCREEN_HEIGHT = 600
# SCREEN_TITLE = "Pac-Man"
# TILE_SIZE = 32
#
# # Couleurs utilisées
# PACMAN_COLOR = arcade.color.YELLOW
# WALL_COLOR = arcade.color.BLUE
# POINT_COLOR = arcade.color.WHITE
#
# # Directions possibles
# UP = 0
# DOWN = 1
# LEFT = 2
# RIGHT = 3
#
# # Intervalle de mouvement (plus haut = plus lent)
# MOVE_INTERVAL = 0.00000001
#
# # Récompenses et pénalités
# REWARD_POINT = 10
# REWARD_GHOST = -100
# REWARD_WALL = -10
# REWARD_DEFAULT = -1
# REWARD_MOVE_AWAY_FROM_GHOST = 1   # Récompense pour s'éloigner des fantômes
# REWARD_MOVE_TOWARDS_GHOST = -1    # Pénalité pour se rapprocher des fantômes
#
#
#
#
# class QTable:
#     def __init__(self, learning_rate=1, discount_factor=0.9):
#         self.q_values = {}  # Dictionnaire pour stocker les valeurs Q
#         self.learning_rate = learning_rate
#         self.discount_factor = discount_factor
#
#     def get(self, state, action):
#         return self.q_values.get((state, action), 0.0)
#
#     def set(self, state, action, value):
#         self.q_values[(state, action)] = value
#
#     def update(self, state, action, reward, next_state):
#         old_value = self.get(state, action)
#         future_rewards = [self.get(next_state, a) for a in [UP, DOWN, LEFT, RIGHT]]
#         learned_value = reward + self.discount_factor * max(future_rewards)
#         new_value = old_value + self.learning_rate * (learned_value - old_value)
#         self.set(state, action, new_value)
#
#     def best_action(self, state):
#         q_values = {action: self.get(state, action) for action in [UP, DOWN, LEFT, RIGHT]}
#         max_value = max(q_values.values())
#         best_actions = [action for action, value in q_values.items() if value == max_value]
#         return random.choice(best_actions)  # Briser les égalités au hasard
#
#     def save(self, filename):
#         with open(filename, 'wb') as f:
#             pickle.dump(self.q_values, f)
#
#     def load(self, filename):
#         try:
#             with open(filename, 'rb') as f:
#                 self.q_values = pickle.load(f)
#         except FileNotFoundError:
#             self.q_values = {}
#
#
# class PacManGame(arcade.Window):
#     def __init__(self):
#         super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
#         arcade.set_background_color(arcade.color.BLACK)
#
#         self.agent = PacmanAgent(self)
#         self.agent.load_qtable('pacman_qtable.pkl')
#         self.episode = 1  # Compteur d'épisodes
#         self.score = 0
#
#
#         # Labyrinthe dessiné par le client
#         self.grid = [
#             "#####################",
#             "#....#.........#....#",
#             "#.##.#.#######.#.##.#",
#             "#.#...............#.#",
#             "#.#.##.###..##.##.#.#",
#             "#......#.....#......#",
#             "#.#.##.#######.##.#.#",
#             "#.#...............#.#",
#             "#.##.#.#######.#.##.#",
#             "#....#.........#....#",
#             "#####################",
#
#         ]
#
#         # Position initiale de Pac-Man
#         self.pacman_x = 1
#         self.pacman_y = 1
#         self.pacman_direction = RIGHT
#         self.requested_direction = RIGHT  # Direction demandée par le joueur
#
#         # Position initiale des fantômes avec types et couleurs
#         self.ghosts = [
#             {"x": 22, "y": 2, "direction": LEFT, "type": "Blinky", "color": arcade.color.RED},
#             {"x": 20, "y": 12, "direction": LEFT, "type": "Pinky", "color": arcade.color.PINK},
#             {"x": 21, "y": 9, "direction": RIGHT, "type": "Inky", "color": arcade.color.CYAN},
#         ]
#
#         self.points = []  # Liste des positions des points à récolter
#         self.game_over = False  # Indicateur pour vérifier la fin de la partie
#         self.victory = False  # Indicateur pour la victoire
#         self.setup_game()
#
#         # Gestion du temps pour ralentir les mouvements
#         self.time_since_last_move = 0
#
#     def setup_game(self):
#         """Initialisation des points à récolter."""
#         for y, row in enumerate(self.grid):
#             for x, cell in enumerate(row):
#                 if cell == ".":
#                     self.points.append((x, y))
#
#     def on_draw(self):
#         """Dessiner tous les éléments du jeu."""
#         arcade.start_render()
#
#         # if self.game_over:
#         #     # Affichage de "Game Over" si la partie est terminée
#         #     arcade.draw_text(
#         #         "Game Over",
#         #         SCREEN_WIDTH // 2,
#         #         SCREEN_HEIGHT // 2,
#         #         arcade.color.RED,
#         #         36,
#         #         anchor_x="center",
#         #     )
#         #     return
#
#         # if self.victory:
#         #     # Affichage de "Victory" si toutes les pièces sont ramassées
#         #     arcade.draw_text(
#         #         "Victory!",
#         #         SCREEN_WIDTH // 2,
#         #         SCREEN_HEIGHT // 2,
#         #         arcade.color.GREEN,
#         #         36,
#         #         anchor_x="center",
#         #     )
#         #     return
#
#         # Création du labyrinthe
#         for y, row in enumerate(self.grid):
#             for x, cell in enumerate(row):
#                 if cell == "#":
#                     arcade.draw_rectangle_filled(
#                         x * TILE_SIZE + TILE_SIZE // 2,
#                         SCREEN_HEIGHT - (y * TILE_SIZE + TILE_SIZE // 2),
#                         TILE_SIZE,
#                         TILE_SIZE,
#                         WALL_COLOR,
#                     )
#
#         # Création des points
#         for x, y in self.points:
#             arcade.draw_circle_filled(
#                 x * TILE_SIZE + TILE_SIZE // 2,
#                 SCREEN_HEIGHT - (y * TILE_SIZE + TILE_SIZE // 2),
#                 5,
#                 POINT_COLOR,
#             )
#
#         # Création de Pac-Man
#         arcade.draw_circle_filled(
#             self.pacman_x * TILE_SIZE + TILE_SIZE // 2,
#             SCREEN_HEIGHT - (self.pacman_y * TILE_SIZE + TILE_SIZE // 2),
#             TILE_SIZE // 2,
#             PACMAN_COLOR,
#         )
#
#         # Création des fantômes avec leurs couleurs respectives
#         for ghost in self.ghosts:
#             arcade.draw_circle_filled(
#                 ghost["x"] * TILE_SIZE + TILE_SIZE // 2,
#                 SCREEN_HEIGHT - (ghost["y"] * TILE_SIZE + TILE_SIZE // 2),
#                 TILE_SIZE // 2,
#                 ghost["color"],
#             )
#
#         # Afficher le numéro de l'épisode
#         arcade.draw_text(
#             f"Épisode : {self.episode}",
#             10,
#             SCREEN_HEIGHT - (SCREEN_HEIGHT - 40),  # Ajuster la position Y pour éviter le chevauchement
#             arcade.color.WHITE,
#             14,
#         )
#
#         # Afficher le score actuel
#         arcade.draw_text(
#             f"Score : {self.score}",
#             10,
#             SCREEN_HEIGHT - (SCREEN_HEIGHT - 20),  # Ajuster la position Y pour éviter le chevauchement
#             arcade.color.WHITE,
#             14,
#         )
#
#     def on_update(self, delta_time):
#         """Mise à jour des déplacements et des actions du jeu."""
#         if self.game_over or self.victory:
#             self.reset_game()
#             self.episode += 1
#             return
#
#         # Gestion de la vitesse de déplacement
#         self.time_since_last_move += delta_time
#         if self.time_since_last_move < MOVE_INTERVAL:
#             return  # Si l'intervalle n'est pas atteint, on ne bouge pas
#
#         self.time_since_last_move = 0  # Réinitialisation du timer
#
#         # Obtenir l'état actuel
#         current_state = self.agent.get_state()
#
#         # Calculer la distance minimale aux fantômes avant le mouvement
#         min_distance_before = min(
#             abs(ghost["x"] - self.pacman_x) + abs(ghost["y"] - self.pacman_y) for ghost in self.ghosts
#         )
#
#         # L'agent choisit une action
#         action = self.agent.choose_action()
#         self.pacman_direction = action
#
#         # Calcul de la nouvelle position
#         new_x, new_y = self.pacman_x, self.pacman_y
#         if action == UP:
#             new_y -= 1
#         elif action == DOWN:
#             new_y += 1
#         elif action == LEFT:
#             new_x -= 1
#         elif action == RIGHT:
#             new_x += 1
#
#         # Initialiser la récompense pour ce mouvement
#         reward = REWARD_DEFAULT  # Petite pénalité pour chaque mouvement
#         self.score += REWARD_DEFAULT  # Mettre à jour le score
#
#         # Vérifier si le mouvement est possible
#         if self.grid[new_y][new_x] != "#":
#             # Mouvement possible
#             self.pacman_x, self.pacman_y = new_x, new_y
#         else:
#             # Mouvement bloqué par un mur
#             reward += REWARD_WALL  # Pénalité pour avoir heurté un mur
#             self.score += REWARD_WALL  # Mettre à jour le score
#
#         # Récolte des points
#         if (self.pacman_x, self.pacman_y) in self.points:
#             self.points.remove((self.pacman_x, self.pacman_y))
#             reward += REWARD_POINT  # Récompense pour avoir collecté un point
#             self.score += REWARD_POINT  # Mettre à jour le score
#
#         # Vérifier la collision avec les fantômes (après le mouvement de Pac-Man)
#         for ghost in self.ghosts:
#             if ghost["x"] == self.pacman_x and ghost["y"] == self.pacman_y:
#                 reward += REWARD_GHOST  # Pénalité pour avoir été attrapé
#                 self.score += REWARD_GHOST  # Mettre à jour le score
#                 self.game_over = True
#                 break
#
#         # Calculer la distance minimale aux fantômes après le mouvement
#         min_distance_after = min(
#             abs(ghost["x"] - self.pacman_x) + abs(ghost["y"] - self.pacman_y) for ghost in self.ghosts
#         )
#
#         # Ajuster la récompense en fonction de la distance aux fantômes
#         if min_distance_after > min_distance_before:
#             # Pac-Man s'est éloigné des fantômes
#             reward += REWARD_MOVE_AWAY_FROM_GHOST  # Récompense pour s'éloigner
#             self.score += REWARD_MOVE_AWAY_FROM_GHOST
#         elif min_distance_after < min_distance_before:
#             # Pac-Man s'est rapproché des fantômes
#             reward += REWARD_MOVE_TOWARDS_GHOST  # Pénalité pour se rapprocher
#             self.score += REWARD_MOVE_TOWARDS_GHOST
#
#         # Vérifier la victoire
#         if not self.points:
#             self.victory = True
#             reward += REWARD_POINT * 10  # Récompense supplémentaire pour la victoire
#             self.score += REWARD_POINT * 10  # Mettre à jour le score
#
#         # Obtenir le nouvel état
#         new_state = self.agent.get_state()
#
#         # Mettre à jour la table Q
#         self.agent.update_qtable(reward, new_state)
#
#         # Mettre à jour l'état précédent de l'agent
#         self.agent.previous_action = action
#
#         # Déplacements des fantômes
#         for ghost in self.ghosts:
#             if ghost["type"] == "Blinky":
#                 # Blinky suit Pac-Man directement
#                 self.move_ghost_towards_target(ghost, self.pacman_x, self.pacman_y)
#             elif ghost["type"] == "Pinky":
#                 # Pinky tente d'anticiper la position future de Pac-Man
#                 target_x, target_y = self.pacman_x, self.pacman_y
#                 if self.pacman_direction == UP:
#                     target_y -= 4
#                 elif self.pacman_direction == DOWN:
#                     target_y += 4
#                 elif self.pacman_direction == LEFT:
#                     target_x -= 4
#                 elif self.pacman_direction == RIGHT:
#                     target_x += 4
#
#                 # Limiter la cible aux limites du labyrinthe
#                 target_x = max(0, min(len(self.grid[0]) - 1, target_x))
#                 target_y = max(0, min(len(self.grid) - 1, target_y))
#
#                 self.move_ghost_towards_target(ghost, target_x, target_y)
#             elif ghost["type"] == "Inky":
#                 # Inky suit souvent Blinky
#                 blinky = next((g for g in self.ghosts if g["type"] == "Blinky"), None)
#                 if blinky:
#                     self.move_ghost_towards_target(ghost, blinky["x"], blinky["y"])
#                 else:
#                     self.move_ghost_randomly(ghost)
#             else:
#                 # Comportement par défaut
#                 self.move_ghost_randomly(ghost)
#
#             # Vérifier la collision avec Pac-Man après le déplacement des fantômes
#             if ghost["x"] == self.pacman_x and ghost["y"] == self.pacman_y:
#                 reward += REWARD_GHOST  # Pénalité pour avoir été attrapé
#                 self.score += REWARD_GHOST  # Mettre à jour le score
#                 self.game_over = True
#                 break
#
#     def move_ghost_towards_target(self, ghost, target_x, target_y):
#         """Déplace le fantôme vers une cible donnée."""
#         possible_directions = []
#
#         # Vérifier les directions possibles en évitant les murs
#         if self.grid[ghost["y"] - 1][ghost["x"]] != "#":  # UP
#             possible_directions.append(UP)
#         if self.grid[ghost["y"] + 1][ghost["x"]] != "#":  # DOWN
#             possible_directions.append(DOWN)
#         if self.grid[ghost["y"]][ghost["x"] - 1] != "#":  # LEFT
#             possible_directions.append(LEFT)
#         if self.grid[ghost["y"]][ghost["x"] + 1] != "#":  # RIGHT
#             possible_directions.append(RIGHT)
#
#         # Choisir la direction qui réduit la distance à la cible
#         min_distance = float('inf')
#         best_direction = None
#         for direction in possible_directions:
#             new_x, new_y = ghost["x"], ghost["y"]
#             if direction == UP:
#                 new_y -= 1
#             elif direction == DOWN:
#                 new_y += 1
#             elif direction == LEFT:
#                 new_x -= 1
#             elif direction == RIGHT:
#                 new_x += 1
#             distance = abs(new_x - target_x) + abs(new_y - target_y)
#             if distance < min_distance:
#                 min_distance = distance
#                 best_direction = direction
#
#         if best_direction is not None:
#             ghost["direction"] = best_direction
#             # Déplacer le fantôme dans la direction choisie
#             if ghost["direction"] == UP:
#                 ghost["y"] -= 1
#             elif ghost["direction"] == DOWN:
#                 ghost["y"] += 1
#             elif ghost["direction"] == LEFT:
#                 ghost["x"] -= 1
#             elif ghost["direction"] == RIGHT:
#                 ghost["x"] += 1
#         else:
#             # Si bloqué, bouger aléatoirement
#             self.move_ghost_randomly(ghost)
#
#     def move_ghost_randomly(self, ghost):
#         """Déplace le fantôme de manière aléatoire."""
#         possible_directions = []
#         if self.grid[ghost["y"] - 1][ghost["x"]] != "#":  # UP
#             possible_directions.append(UP)
#         if self.grid[ghost["y"] + 1][ghost["x"]] != "#":  # DOWN
#             possible_directions.append(DOWN)
#         if self.grid[ghost["y"]][ghost["x"] - 1] != "#":  # LEFT
#             possible_directions.append(LEFT)
#         if self.grid[ghost["y"]][ghost["x"] + 1] != "#":  # RIGHT
#             possible_directions.append(RIGHT)
#
#         if possible_directions:
#             ghost["direction"] = random.choice(possible_directions)
#             if ghost["direction"] == UP:
#                 ghost["y"] -= 1
#             elif ghost["direction"] == DOWN:
#                 ghost["y"] += 1
#             elif ghost["direction"] == LEFT:
#                 ghost["x"] -= 1
#             elif ghost["direction"] == RIGHT:
#                 ghost["x"] += 1
#
#     def reset_game(self):
#         """Réinitialiser les variables du jeu pour recommencer une partie."""
#         self.pacman_x = 1
#         self.pacman_y = 1
#         self.pacman_direction = RIGHT
#         self.requested_direction = RIGHT
#         # Réinitialiser les fantômes avec types et couleurs
#         self.ghosts = [
#             {"x": 22, "y": 2, "direction": LEFT, "type": "Blinky", "color": arcade.color.RED},
#             {"x": 20, "y": 12, "direction": LEFT, "type": "Pinky", "color": arcade.color.PINK},
#             {"x": 21, "y": 9, "direction": RIGHT, "type": "Inky", "color": arcade.color.CYAN},
#         ]
#         self.points = []
#         self.game_over = False
#         self.victory = False
#         self.setup_game()
#         self.time_since_last_move = 0
#         self.score = 0
#
#         # Réinitialiser l'état de l'agent
#         self.agent.previous_state = None
#         self.agent.previous_action = None
#
#     def on_close(self):
#         # Sauvegarder la table Q de l'agent Pac-Man
#         self.agent.save_qtable('pacman_qtable.pkl')
#         super().on_close()
#
#     def on_key_press(self, key, modifiers):
#         """Gérer les entrées clavier pour diriger Pac-Man."""
#         if key == arcade.key.UP:
#             self.requested_direction = UP
#         elif key == arcade.key.DOWN:
#             self.requested_direction = DOWN
#         elif key == arcade.key.LEFT:
#             self.requested_direction = LEFT
#         elif key == arcade.key.RIGHT:
#             self.requested_direction = RIGHT
#         elif key == arcade.key.R and (self.game_over or self.victory):
#             self.reset_game()
#
#
# class PacmanAgent:
#     def __init__(self, game):
#         self.game = game
#         self.qtable = QTable()
#         self.previous_state = None
#         self.previous_action = None
#
#     def get_state(self):
#         # Taille du champ de vision (doit être un entier impair)
#         vision_range = 3  # Champ de vision de 3x3 autour de Pac-Man
#
#         # Obtenir la position de Pac-Man
#         pacman_x, pacman_y = self.game.pacman_x, self.game.pacman_y
#
#         # Initialiser la liste du champ de vision
#         vision = []
#
#         # Parcourir les positions autour de Pac-Man
#         for dy in range(-vision_range, vision_range + 1):
#             for dx in range(-vision_range, vision_range + 1):
#                 x = pacman_x + dx
#                 y = pacman_y + dy
#
#                 # Vérifier les limites du labyrinthe
#                 if 0 <= y < len(self.game.grid) and 0 <= x < len(self.game.grid[0]):
#                     cell = self.game.grid[y][x]
#                     # Vérifier si un fantôme est présent
#                     ghost_here = any(ghost["x"] == x and ghost["y"] == y for ghost in self.game.ghosts)
#                     if ghost_here:
#                         vision.append('G')  # Fantôme
#                     elif cell == '#':
#                         vision.append('#')  # Mur
#                     elif (x, y) in self.game.points:
#                         vision.append('.')
#                     else:
#                         vision.append(' ')
#                 else:
#                     # En dehors des limites du labyrinthe
#                     vision.append('#')
#
#         # Convertir la vision en tuple pour pouvoir l'utiliser comme clé dans le dictionnaire
#         vision = tuple(vision)
#
#         # L'état est la vision autour de Pac-Man
#         return vision
#
#     def choose_action(self):
#         state = self.get_state()
#         epsilon = 0.1  # Taux d'exploration
#         if random.uniform(0, 1) < epsilon:
#             return random.choice([UP, DOWN, LEFT, RIGHT])
#         else:
#             return self.qtable.best_action(state)
#
#     def update_qtable(self, reward, new_state):
#         if self.previous_state is not None and self.previous_action is not None:
#             self.qtable.update(self.previous_state, self.previous_action, reward, new_state)
#         self.previous_state = new_state
#
#     def save_qtable(self, filename):
#         self.qtable.save(filename)
#
#     def load_qtable(self, filename):
#         self.qtable.load(filename)
#
#
# if __name__ == "__main__":
#     game = PacManGame()
#     arcade.run()




import arcade
import random
import pickle

# Dimensions de la fenêtre et du labyrinthe
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Pac-Man avec Q-Learning"
TILE_SIZE = 32  # Taille des tuiles pour l'affichage

# Définition des constantes
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

ACTIONS = [UP, DOWN, LEFT, RIGHT]

REWARD_POINT = 10
REWARD_POWER_PELLET = 50  # Récompense pour un power-pellet
REWARD_EAT_GHOST = 200    # Récompense pour avoir mangé un fantôme
REWARD_GHOST = -100
REWARD_WALL = -10
REWARD_DEFAULT = -1
REWARD_MOVE_AWAY_FROM_GHOST = 1
REWARD_MOVE_TOWARDS_GHOST = -1

POWER_UP_DURATION = 30  # Nombre de tours pendant lesquels Pac-Man est puissant

class QTable:
    def __init__(self, learning_rate=1, discount_factor=0.9):
        self.q_values = {}  # Dictionnaire pour stocker les valeurs Q
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def get(self, state, action):
        return self.q_values.get((state, action), 0.0)

    def set(self, state, action, value):
        self.q_values[(state, action)] = value

    def update(self, state, action, reward, next_state):
        old_value = self.get(state, action)
        future_rewards = [self.get(next_state, a) for a in ACTIONS]
        learned_value = reward + self.discount_factor * max(future_rewards)
        new_value = old_value + self.learning_rate * (learned_value - old_value)
        self.set(state, action, new_value)

    def best_action(self, state):
        q_values = {action: self.get(state, action) for action in ACTIONS}
        max_value = max(q_values.values())
        best_actions = [action for action, value in q_values.items() if value == max_value]
        return random.choice(best_actions)

    def save(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.q_values, f)

    def load(self, filename):
        try:
            with open(filename, 'rb') as f:
                self.q_values = pickle.load(f)
        except FileNotFoundError:
            self.q_values = {}

class PacmanAgent:
    def __init__(self, game):
        self.game = game
        self.qtable = QTable()
        self.previous_state = None
        self.previous_action = None

    def get_state(self):
        # Implémentation du champ de vision
        vision_range = 3
        pacman_x, pacman_y = self.game.pacman_x, self.game.pacman_y
        vision = []

        for dy in range(-vision_range, vision_range + 1):
            for dx in range(-vision_range, vision_range + 1):
                x = pacman_x + dx
                y = pacman_y + dy

                if 0 <= y < len(self.game.grid) and 0 <= x < len(self.game.grid[0]):
                    cell = self.game.grid[y][x]
                    ghost_here = any(ghost["x"] == x and ghost["y"] == y for ghost in self.game.ghosts)
                    if ghost_here:
                        vision.append('G')
                    elif cell == '#':
                        vision.append('#')
                    elif (x, y) in self.game.power_pellets:
                        vision.append('o')
                    elif (x, y) in self.game.points:
                        vision.append('.')
                    else:
                        vision.append(' ')
                else:
                    vision.append('#')

        # Inclure l'état puissant de Pac-Man
        powered_up = self.game.power_up_counter > 0
        vision.append(powered_up)

        return tuple(vision)

    def choose_action(self):
        state = self.get_state()
        epsilon = 0.1  # Taux d'exploration
        if random.uniform(0, 1) < epsilon:
            return random.choice(ACTIONS)
        else:
            return self.qtable.best_action(state)

    def update_qtable(self, reward, new_state):
        if self.previous_state is not None and self.previous_action is not None:
            self.qtable.update(self.previous_state, self.previous_action, reward, new_state)
        self.previous_state = new_state

    def save_qtable(self, filename):
        self.qtable.save(filename)

    def load_qtable(self, filename):
        self.qtable.load(filename)

class PacManGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.grid = [
            "#####################",
            "#o...#.........#...o#",
            "#.##.#.#######.#.##.#",
            "#.#...............#.#",
            "#.#.##.##   ##.##.#.#",
            "#......#     #......#",
            "#.#.##.#######.##.#.#",
            "#.#...............#.#",
            "#.##.#.#######.#.##.#",
            "#o...#.........#...o#",
            "#####################",
        ]
        self.tile_size = TILE_SIZE
        self.width = len(self.grid[0]) * self.tile_size
        self.height = len(self.grid) * self.tile_size
        self.set_size(self.width, self.height)
        self.agent = PacmanAgent(self)
        self.agent.load_qtable('pacman_qtable.pkl')
        self.setup()

    def setup(self):
        self.score = 0
        self.power_up_counter = 0
        self.game_over = False
        self.victory = False

        self.pacman_x = 1
        self.pacman_y = 1
        self.pacman_direction = RIGHT

        self.points = []
        self.power_pellets = []
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell == ".":
                    self.points.append((x, y))
                elif cell == "o":
                    self.power_pellets.append((x, y))

        self.ghosts = [
            {"x": 14, "y": 9, "direction": LEFT, "type": "Blinky", "start_x": 14, "start_y": 9},
        ]

        # Charger les sprites
        self.wall_list = arcade.SpriteList()
        self.point_list = arcade.SpriteList()
        self.power_pellet_list = arcade.SpriteList()
        self.ghost_list = arcade.SpriteList()
        self.pacman_sprite = arcade.SpriteSolidColor(self.tile_size, self.tile_size, arcade.color.YELLOW)

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell == "#":
                    wall = arcade.SpriteSolidColor(self.tile_size, self.tile_size, arcade.color.BLUE)
                    wall.center_x = x * self.tile_size + self.tile_size / 2
                    wall.center_y = (len(self.grid) - y - 1) * self.tile_size + self.tile_size / 2
                    self.wall_list.append(wall)
                elif cell == ".":
                    point = arcade.SpriteSolidColor(self.tile_size // 4, self.tile_size // 4, arcade.color.WHITE)
                    point.center_x = x * self.tile_size + self.tile_size / 2
                    point.center_y = (len(self.grid) - y - 1) * self.tile_size + self.tile_size / 2
                    self.point_list.append(point)
                elif cell == "o":
                    pellet = arcade.SpriteSolidColor(self.tile_size // 2, self.tile_size // 2, arcade.color.GOLD)
                    pellet.center_x = x * self.tile_size + self.tile_size / 2
                    pellet.center_y = (len(self.grid) - y - 1) * self.tile_size + self.tile_size / 2
                    self.power_pellet_list.append(pellet)

        for ghost in self.ghosts:
            ghost_sprite = arcade.SpriteSolidColor(self.tile_size, self.tile_size, arcade.color.RED)
            ghost_sprite.center_x = ghost["x"] * self.tile_size + self.tile_size / 2
            ghost_sprite.center_y = (len(self.grid) - ghost["y"] - 1) * self.tile_size + self.tile_size / 2
            ghost["sprite"] = ghost_sprite
            self.ghost_list.append(ghost_sprite)

        self.pacman_sprite.center_x = self.pacman_x * self.tile_size + self.tile_size / 2
        self.pacman_sprite.center_y = (len(self.grid) - self.pacman_y - 1) * self.tile_size + self.tile_size / 2

    def on_draw(self):
        arcade.start_render()
        self.wall_list.draw()
        self.point_list.draw()
        self.power_pellet_list.draw()
        self.ghost_list.draw()
        self.pacman_sprite.draw()

        # Afficher le score
        arcade.draw_text(f"Score: {self.score}", 10, 10, arcade.color.WHITE, 14)

        # Afficher le message de fin
        if self.game_over:
            arcade.draw_text("GAME OVER", self.width / 2, self.height / 2, arcade.color.RED, 50, anchor_x="center")
        elif self.victory:
            arcade.draw_text("VICTOIRE!", self.width / 2, self.height / 2, arcade.color.GREEN, 50, anchor_x="center")

    def on_update(self, delta_time):
        if self.game_over or self.victory:
            return

        # Obtenir l'état actuel
        current_state = self.agent.get_state()

        # L'agent choisit une action
        action = self.agent.choose_action()
        self.pacman_direction = action

        # Calcul de la nouvelle position
        new_x, new_y = self.pacman_x, self.pacman_y
        if action == UP:
            new_y -= 1
        elif action == DOWN:
            new_y += 1
        elif action == LEFT:
            new_x -= 1
        elif action == RIGHT:
            new_x += 1

        # Initialiser la récompense pour ce mouvement
        reward = REWARD_DEFAULT
        self.score += REWARD_DEFAULT

        # Vérifier si le mouvement est possible
        if self.grid[new_y][new_x] != "#":
            # Mouvement possible
            self.pacman_x, self.pacman_y = new_x, new_y
            self.pacman_sprite.center_x = self.pacman_x * self.tile_size + self.tile_size / 2
            self.pacman_sprite.center_y = (len(self.grid) - self.pacman_y - 1) * self.tile_size + self.tile_size / 2
        else:
            # Mouvement bloqué par un mur
            reward += REWARD_WALL
            self.score += REWARD_WALL

        # Récolte des points
        if (self.pacman_x, self.pacman_y) in self.points:
            self.points.remove((self.pacman_x, self.pacman_y))
            reward += REWARD_POINT
            self.score += REWARD_POINT
            # Retirer le point de l'affichage
            for point in self.point_list:
                if (point.center_x == self.pacman_sprite.center_x) and (point.center_y == self.pacman_sprite.center_y):
                    point.remove_from_sprite_lists()
                    break

        # Récolte des power-pellets
        if (self.pacman_x, self.pacman_y) in self.power_pellets:
            self.power_pellets.remove((self.pacman_x, self.pacman_y))
            reward += REWARD_POWER_PELLET
            self.score += REWARD_POWER_PELLET
            self.power_up_counter = POWER_UP_DURATION  # Pac-Man devient puissant
            # Retirer le power-pellet de l'affichage
            for pellet in self.power_pellet_list:
                if (pellet.center_x == self.pacman_sprite.center_x) and (pellet.center_y == self.pacman_sprite.center_y):
                    pellet.remove_from_sprite_lists()
                    break

        # Vérifier la victoire (tous les points et power-pellets collectés)
        if not self.points and not self.power_pellets:
            self.victory = True
            reward += REWARD_POINT * 10  # Récompense supplémentaire pour la victoire
            self.score += REWARD_POINT * 10
            # Fin du jeu si victoire
            return

        # Gestion de l'état puissant de Pac-Man
        if self.power_up_counter > 0:
            self.power_up_counter -= 1  # Diminuer le compteur
            self.pacman_sprite.color = arcade.color.YELLOW_ORANGE
        else:
            self.pacman_sprite.color = arcade.color.YELLOW

        # Vérifier la collision avec les fantômes
        for ghost in self.ghosts:
            if ghost["x"] == self.pacman_x and ghost["y"] == self.pacman_y:
                if self.power_up_counter > 0:
                    # Pac-Man mange le fantôme
                    reward += REWARD_EAT_GHOST
                    self.score += REWARD_EAT_GHOST
                    # Réinitialiser le fantôme à sa position de départ
                    ghost["x"] = ghost["start_x"]
                    ghost["y"] = ghost["start_y"]
                    ghost["sprite"].center_x = ghost["x"] * self.tile_size + self.tile_size / 2
                    ghost["sprite"].center_y = (len(self.grid) - ghost["y"] - 1) * self.tile_size + self.tile_size / 2
                else:
                    # Pac-Man est attrapé par le fantôme
                    reward += REWARD_GHOST
                    self.score += REWARD_GHOST
                    self.game_over = True
                    break

        # Déplacements des fantômes
        self.move_ghosts()

        # Vérifier la collision avec les fantômes après leur déplacement
        for ghost in self.ghosts:
            if ghost["x"] == self.pacman_x and ghost["y"] == self.pacman_y:
                if self.power_up_counter > 0:
                    # Pac-Man mange le fantôme
                    reward += REWARD_EAT_GHOST
                    self.score += REWARD_EAT_GHOST
                    # Réinitialiser le fantôme
                    ghost["x"] = ghost["start_x"]
                    ghost["y"] = ghost["start_y"]
                    ghost["sprite"].center_x = ghost["x"] * self.tile_size + self.tile_size / 2
                    ghost["sprite"].center_y = (len(self.grid) - ghost["y"] - 1) * self.tile_size + self.tile_size / 2
                else:
                    # Pac-Man est attrapé par le fantôme
                    reward += REWARD_GHOST
                    self.score += REWARD_GHOST
                    self.game_over = True
                    break

        # Obtenir le nouvel état
        new_state = self.agent.get_state()

        # Mettre à jour la table Q
        self.agent.update_qtable(reward, new_state)

        # Mettre à jour l'état précédent de l'agent
        self.agent.previous_action = action

        # Enregistrer la table Q
        self.agent.save_qtable('pacman_qtable.pkl')

    def move_ghosts(self):
        for ghost in self.ghosts:
            if self.power_up_counter > 0:
                # Fantômes se déplacent aléatoirement lorsqu'ils sont vulnérables
                self.move_ghost_randomly(ghost)
            else:
                if ghost["type"] == "Blinky":
                    self.move_ghost_towards_target(ghost, self.pacman_x, self.pacman_y)
                else:
                    self.move_ghost_randomly(ghost)

            # Mettre à jour la position du sprite du fantôme
            ghost["sprite"].center_x = ghost["x"] * self.tile_size + self.tile_size / 2
            ghost["sprite"].center_y = (len(self.grid) - ghost["y"] - 1) * self.tile_size + self.tile_size / 2

    def move_ghost_towards_target(self, ghost, target_x, target_y):
        """Déplace le fantôme vers une cible donnée."""
        possible_directions = []

        # Vérifier les directions possibles en évitant les murs
        if self.grid[ghost["y"] - 1][ghost["x"]] != "#":  # UP
            possible_directions.append(UP)
        if self.grid[ghost["y"] + 1][ghost["x"]] != "#":  # DOWN
            possible_directions.append(DOWN)
        if self.grid[ghost["y"]][ghost["x"] - 1] != "#":  # LEFT
            possible_directions.append(LEFT)
        if self.grid[ghost["y"]][ghost["x"] + 1] != "#":  # RIGHT
            possible_directions.append(RIGHT)

        # Choisir la direction qui réduit la distance à la cible
        min_distance = float('inf')
        best_direction = None
        for direction in possible_directions:
            new_x, new_y = ghost["x"], ghost["y"]
            if direction == UP:
                new_y -= 1
            elif direction == DOWN:
                new_y += 1
            elif direction == LEFT:
                new_x -= 1
            elif direction == RIGHT:
                new_x += 1
            distance = abs(new_x - target_x) + abs(new_y - target_y)
            if distance < min_distance:
                min_distance = distance
                best_direction = direction

        if best_direction is not None:
            ghost["direction"] = best_direction
            # Déplacer le fantôme dans la direction choisie
            if ghost["direction"] == UP:
                ghost["y"] -= 1
            elif ghost["direction"] == DOWN:
                ghost["y"] += 1
            elif ghost["direction"] == LEFT:
                ghost["x"] -= 1
            elif ghost["direction"] == RIGHT:
                ghost["x"] += 1
        else:
            # Si bloqué, bouger aléatoirement
            self.move_ghost_randomly(ghost)

    def move_ghost_randomly(self, ghost):
        """Déplace le fantôme de manière aléatoire."""
        possible_directions = []
        if self.grid[ghost["y"] - 1][ghost["x"]] != "#":  # UP
            possible_directions.append(UP)
        if self.grid[ghost["y"] + 1][ghost["x"]] != "#":  # DOWN
            possible_directions.append(DOWN)
        if self.grid[ghost["y"]][ghost["x"] - 1] != "#":  # LEFT
            possible_directions.append(LEFT)
        if self.grid[ghost["y"]][ghost["x"] + 1] != "#":  # RIGHT
            possible_directions.append(RIGHT)

        if possible_directions:
            ghost["direction"] = random.choice(possible_directions)
            if ghost["direction"] == UP:
                ghost["y"] -= 1
            elif ghost["direction"] == DOWN:
                ghost["y"] += 1
            elif ghost["direction"] == LEFT:
                ghost["x"] -= 1
            elif ghost["direction"] == RIGHT:
                ghost["x"] += 1

    def on_key_press(self, key, modifiers):
        """Permet de redémarrer le jeu avec la touche R."""
        if key == arcade.key.R:
            self.setup()

if __name__ == "__main__":
    game = PacManGame()
    arcade.run()
