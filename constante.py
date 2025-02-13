MAZE = """
xxxxxxxxxxxxxxxxx
xo.............ox
x.xxx.xxxxx.xxx.x
x.x...........x.x
x.x.xxx.x.xxx.x.x
x...x.....x...x.x
x.x.x.xxxxx.x.x.x
x.x...........x.x
x.xxx.xxxxx.xxx.x
x.x...........x.x
x.x.xxx.x.xxx.x.x
x...x.....x...x.x
x.x.x.xxxxx.x.x.x
x.x...........x.x
x.xxx.xxxxx.xxx.x
xo.............ox
xxxxxxxxxxxxxxxxx
"""

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
REWARD_OUT     = -500       # Sortie du labyrinthe
REWARD_WALL    = -200       # Collision avec un mur
REWARD_REPEAT  = -5         # Malus pour revisiter une case
REWARD_WIN     = 500000     # Récompense de victoire (tous les pellets ramassés)
REWARD_PELLET  = 5000       # Ramasser un pellet (increased reward)
REWARD_DEFAULT = -2         # Mouvement "normal" (adoucit pour un labyrinthe plus vaste)
REWARD_GHOST   = -100000    # Collision avec le fantôme
REWARD_EAT_GHOST = 20000     # Récompense pour avoir manger un fantome
POWER_PELLET_DURATION = 40   # Timming pour la power pellet

WIN = 1
LOOSE = 0

FILE_AGENT = 'mouse.qtable'

# Paramètre graphique
SPRITE_SIZE = 64
