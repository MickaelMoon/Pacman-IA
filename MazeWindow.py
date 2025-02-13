###############################################################################
# Fenêtre (affichage avec Arcade)
###############################################################################

import arcade
from constante import (
    SPEED, SPRITE_SIZE, TILE_PELLET, TILE_POWER_PELLET, TILE_WALL,
    ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT, MOVES
)


class MazeWindow(arcade.Window):
    def __init__(self, agent):
        super().__init__(SPRITE_SIZE * agent.env.width,
                         SPRITE_SIZE * agent.env.height,
                         "Pacman AI")
        self.agent = agent
        self.env = agent.env
        self.manual_mode = False  # Mode manuel désactivé par défaut
        self.current_direction = None  # Direction courante pour le mode manuel
        self.move_timer = 0  # Timer pour contrôler la vitesse de déplacement
        self.move_delay = 0.15  # Délai entre chaque déplacement en secondes
        arcade.set_background_color(arcade.color.BLACK)
        self.set_update_rate(1 / SPEED)

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
        for i, ghost_position in enumerate(self.env.ghost_positions):
            ghost_sprite = 'assets/ghost.png' if i == 0 else 'assets/ghost2.png'
            ghost = self.create_sprite(ghost_sprite, ghost_position)
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

    def on_update(self, delta_time):
        if (not self.env.pellet_manager.are_all_pellets_collected() and
            self.agent.position not in self.env.ghost_positions):
            
            if not self.manual_mode:
                self.agent.do()
            else:
                # Gestion du délai de déplacement
                self.move_timer += delta_time
                if self.current_direction and self.move_timer >= self.move_delay:
                    self.move_timer = 0  # Reset du timer
                    self.move_player(self.current_direction)
                # En mode manuel, on continue de faire bouger les fantômes
                self.env.move_ghosts(self.agent.position, self.agent.last_action)

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
        elif key == arcade.key.M:  # Touche M pour basculer le mode manuel
            self.manual_mode = not self.manual_mode
            self.current_direction = None  # Réinitialise la direction quand on change de mode
            print("Mode manuel:" + (" activé" if self.manual_mode else " désactivé"))
        
        if self.manual_mode:  # Contrôles manuels
            if key == arcade.key.UP:
                self.current_direction = ACTION_UP
            elif key == arcade.key.DOWN:
                self.current_direction = ACTION_DOWN
            elif key == arcade.key.LEFT:
                self.current_direction = ACTION_LEFT
            elif key == arcade.key.RIGHT:
                self.current_direction = ACTION_RIGHT

    def on_key_release(self, key, modifiers):
        if self.manual_mode:
            # Arrête le mouvement seulement si la touche relâchée correspond à la direction courante
            if (key == arcade.key.UP and self.current_direction == ACTION_UP) or \
               (key == arcade.key.DOWN and self.current_direction == ACTION_DOWN) or \
               (key == arcade.key.LEFT and self.current_direction == ACTION_LEFT) or \
               (key == arcade.key.RIGHT and self.current_direction == ACTION_RIGHT):
                self.current_direction = None

    def move_player(self, action):
        direction = MOVES[action]  # Convertit l'action en direction
        new_pos = (self.agent.position[0] + direction[0], 
                  self.agent.position[1] + direction[1])
        # Vérifier si le mouvement est valide (pas de mur)
        if new_pos not in self.env.maze or self.env.maze[new_pos] != TILE_WALL:
            new_position, reward = self.env.move(self.agent.position, action)
            self.agent.position = new_position
            self.agent.last_action = action  # On stocke l'action et non la direction
            self.agent.score += reward