###############################################################################
# Fenêtre (affichage avec Arcade)
###############################################################################

import arcade
from constante import SPRITE_SIZE, TILE_PELLET, TILE_POWER_PELLET, TILE_WALL


class MazeWindow(arcade.Window):
    def __init__(self, agent):
        super().__init__(SPRITE_SIZE * agent.env.width,
                         SPRITE_SIZE * agent.env.height,
                         "Pacman AI")
        self.agent = agent
        self.env = agent.env
        arcade.set_background_color(arcade.color.BLACK)
        self.set_update_rate(1 / 1200)

    def schedule(self, callback, interval):
        arcade.schedule(callback, interval)
        
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