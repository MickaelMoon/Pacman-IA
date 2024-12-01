import arcade
import random

# Dimensions de la fenêtre et du labyrinthe
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Pac-Man"
TILE_SIZE = 32

# Couleurs utilisées
PACMAN_COLOR = arcade.color.YELLOW
WALL_COLOR = arcade.color.BLUE
POINT_COLOR = arcade.color.WHITE

# Directions possibles
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

# Intervalle de mouvement (plus haut = plus lent)
MOVE_INTERVAL = 0.1

# Récompenses et pénalités
REWARD_POINT = 10
REWARD_GHOST = -100
REWARD_WALL = -10
REWARD_DEFAULT = -1

class PacManGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        # Labyrinthe dessiné par le client
        self.grid = [
            "########################",
            "#..........##..........#",
            "#.####.###.##.###.####.#",
            "#.####.###.##.###.####.#",
            "#.####.###.##.###.####.#",
            "#......................#",
            "#.####.##.######.##.####",
            "#.####.##.######.##.####",
            "#......##....##........#",
            "######.#####.##.#####.##",
            "######.#####.##.#####.##",
            "######.#####.##.#####.##",
            "######................##",
            "########################",
        ]

        # Position initiale de Pac-Man
        self.pacman_x = 1
        self.pacman_y = 1
        self.pacman_direction = RIGHT
        self.requested_direction = RIGHT  # Direction demandée par le joueur

        # Position initiale des fantômes
        self.ghosts = [
            {"x": 10, "y": 8, "direction": LEFT},
            {"x": 10, "y": 12, "direction": LEFT},
            {"x": 14, "y": 8, "direction": RIGHT},
        ]

        self.points = []  # Liste des positions des points à récolter
        self.game_over = False  # Indicateur pour vérifier la fin de la partie
        self.victory = False  # Indicateur pour la victoire
        self.setup_game()

        # Gestion du temps pour ralentir les mouvements
        self.time_since_last_move = 0

    def setup_game(self):
        """Initialisation des points à récolter."""
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell == ".":
                    self.points.append((x, y))

    def on_draw(self):
        """Dessiner tous les éléments du jeu."""
        arcade.start_render()

        if self.game_over:
            # Affichage de "Game Over" si la partie est terminée
            arcade.draw_text(
                "Game Over",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                arcade.color.RED,
                36,
                anchor_x="center",
            )
            return

        if self.victory:
            # Affichage de "Victory" si toutes les pièces sont ramassées
            arcade.draw_text(
                "Victory!",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                arcade.color.GREEN,
                36,
                anchor_x="center",
            )
            return

        # Création du labyrinthe
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell == "#":
                    arcade.draw_rectangle_filled(
                        x * TILE_SIZE + TILE_SIZE // 2,
                        SCREEN_HEIGHT - (y * TILE_SIZE + TILE_SIZE // 2),
                        TILE_SIZE,
                        TILE_SIZE,
                        WALL_COLOR,
                    )

        # Création des points
        for x, y in self.points:
            arcade.draw_circle_filled(
                x * TILE_SIZE + TILE_SIZE // 2,
                SCREEN_HEIGHT - (y * TILE_SIZE + TILE_SIZE // 2),
                5,
                POINT_COLOR,
            )

        # Création de Pac-Man
        arcade.draw_circle_filled(
            self.pacman_x * TILE_SIZE + TILE_SIZE // 2,
            SCREEN_HEIGHT - (self.pacman_y * TILE_SIZE + TILE_SIZE // 2),
            TILE_SIZE // 2,
            PACMAN_COLOR,
        )

        # Création des fantômes
        for ghost in self.ghosts:
            arcade.draw_circle_filled(
                ghost["x"] * TILE_SIZE + TILE_SIZE // 2,
                SCREEN_HEIGHT - (ghost["y"] * TILE_SIZE + TILE_SIZE // 2),
                TILE_SIZE // 2,
                arcade.color.RED,
            )

    def on_update(self, delta_time):
        """Mise à jour des déplacements et des actions du jeu."""
        if self.game_over or self.victory:
            return

        # Gestion de la vitesse de déplacement
        self.time_since_last_move += delta_time
        if self.time_since_last_move < MOVE_INTERVAL:
            return  # Si l'intervalle n'est pas atteint, on ne bouge pas

        self.time_since_last_move = 0  # Réinitialisation du timer

         # Calcul de la position demandée
        requested_x, requested_y = self.pacman_x, self.pacman_y
        if self.requested_direction == UP:
            requested_y -= 1
        elif self.requested_direction == DOWN:
            requested_y += 1
        elif self.requested_direction == LEFT:
            requested_x -= 1
        elif self.requested_direction == RIGHT:
            requested_x += 1

        # Tenter de changer de direction si possible
        if self.requested_direction is not None and self.grid[requested_y][requested_x] != "#":
            # Si la direction demandée est possible, on l'applique
            self.pacman_direction = self.requested_direction
            self.pacman_x, self.pacman_y = requested_x, requested_y
            self.requested_direction = None  # Réinitialiser la direction demandée
        else:
            # Réinitialiser immédiatement la direction demandée si elle est impossible
            self.requested_direction = None

            # Continuer dans la direction actuelle
            current_x, current_y = self.pacman_x, self.pacman_y
            if self.pacman_direction == UP:
                current_y -= 1
            elif self.pacman_direction == DOWN:
                current_y += 1
            elif self.pacman_direction == LEFT:
                current_x -= 1
            elif self.pacman_direction == RIGHT:
                current_x += 1

            # Si le mouvement dans la direction actuelle est possible
            if self.grid[current_y][current_x] != "#":
                self.pacman_x, self.pacman_y = current_x, current_y

        # Récolte des points
        if (self.pacman_x, self.pacman_y) in self.points:
            self.points.remove((self.pacman_x, self.pacman_y))

        if not self.points:
            self.victory = True
            return

        # Déplacements des fantômes
        for ghost in self.ghosts:
            ghost_new_x, ghost_new_y = ghost["x"], ghost["y"]
            if ghost["direction"] == UP:
                ghost_new_y -= 1
            elif ghost["direction"] == DOWN:
                ghost_new_y += 1
            elif ghost["direction"] == LEFT:
                ghost_new_x -= 1
            elif ghost["direction"] == RIGHT:
                ghost_new_x += 1

            if self.grid[ghost_new_y][ghost_new_x] == "#":
                ghost["direction"] = random.choice([UP, DOWN, LEFT, RIGHT])
            else:
                ghost["x"], ghost["y"] = ghost_new_x, ghost_new_y

            # Vérifier la collision avec Pac-Man
            if ghost["x"] == self.pacman_x and ghost["y"] == self.pacman_y:
                self.game_over = True

    def reset_game(self):
        """Réinitialiser les variables du jeu pour recommencer une partie."""
        self.pacman_x = 1
        self.pacman_y = 1
        self.pacman_direction = RIGHT
        self.requested_direction = RIGHT
        self.ghosts = [
            {"x": 10, "y": 8, "direction": LEFT},
            {"x": 10, "y": 12, "direction": LEFT},
            {"x": 14, "y": 8, "direction": RIGHT},
        ]
        self.points = []
        self.game_over = False
        self.victory = False
        self.setup_game()
        self.time_since_last_move = 0

    def on_key_press(self, key, modifiers):
        """Gérer les entrées clavier pour diriger Pac-Man."""
        if key == arcade.key.UP:
            self.requested_direction = UP
        elif key == arcade.key.DOWN:
            self.requested_direction = DOWN
        elif key == arcade.key.LEFT:
            self.requested_direction = LEFT
        elif key == arcade.key.RIGHT:
            self.requested_direction = RIGHT
        elif key == arcade.key.R and (self.game_over or self.victory):
            self.reset_game()


if __name__ == "__main__":
    game = PacManGame()
    arcade.run()
