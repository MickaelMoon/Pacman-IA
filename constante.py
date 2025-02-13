MAZE = """
xxxxxxxxxxx
xo.......ox
x.xxx.xxx.x
x.x.....x.x
x.x.x.x.x.x
x...x.x...x
x.x.xxx.x.x
x.x.....x.x
x.xxx.xxx.x
xo.......ox
xxxxxxxxxxx
"""

FILE_AGENT = 'mouse.qtable'

# Constantes pour le labyrinthe
TILE_WALL = 'x'
TILE_PELLET = '.'
TILE_POWER_PELLET = 'o'

# Actions
ACTION_UP = 'U'
ACTION_DOWN = 'D'
ACTION_LEFT = 'L'
ACTION_RIGHT = 'R'
ACTIONS = [ACTION_UP, ACTION_DOWN, ACTION_LEFT, ACTION_RIGHT]

# Déplacements
MOVES = {
    ACTION_UP: (-1, 0),
    ACTION_DOWN: (1, 0),
    ACTION_LEFT: (0, -1),
    ACTION_RIGHT: (0, 1)
}

# Récompenses
REWARD_OUT     = -200       # Sortie du labyrinthe
REWARD_WALL    = -200       # Collision avec un mur
REWARD_REPEAT  = -5         # Malus pour revisiter une case
REWARD_WIN     = 50000      # Récompense de victoire (tous les pellets ramassés)
REWARD_PELLET  = 1000       # Ramasser un pellet (increased reward)
REWARD_DEFAULT = -1         # Mouvement "normal" (adoucit pour un labyrinthe plus vaste)
REWARD_GHOST   = -20000     # Collision avec le fantôme

WIN = 1
LOOSE = 0

# Paramètre graphique
SPRITE_SIZE = 64