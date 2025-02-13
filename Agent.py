###############################################################################
# Agent
###############################################################################

import pickle
from random import random

from matplotlib.pylab import choice
from QTable import QTable
from constante import ACTIONS


class Agent:
    def __init__(self, env, exploration=1.0, exploration_decay=0.99995):
        self.env = env
        self.history = []
        self.score = None
        self.qtable = QTable(learning_rate=0.2, discount_factor=0.95)
        self.exploration = exploration
        self.exploration_decay = exploration_decay
        self.last_action = None
        self.reset()

    def reset(self):
        if self.score is not None:
            self.history.append(self.score)
        self.position = self.env.start
        self.score = 0
        self.env.reset_maze()

    def shake(self, exploration=1.0):
        """Réinitialise l'exploration (par exemple, lors d'un appui sur E)."""
        self.exploration = exploration

    def save(self, filename):
        with open(filename, 'wb') as file:
            pickle.dump((self.qtable.dic, self.history), file)

    def load(self, filename):
        with open(filename, 'rb') as file:
            self.qtable.dic, self.history = pickle.load(file)

    def do(self, action=None):
        """
        Exécute une action, met à jour la Q-table et retourne (action, reward).
        Utilise une vision de taille 5x5.
        """
        current_vision = self.env.get_vision(self.position, vision_size=5)
        current_state = (
            tuple(tuple(row) for row in current_vision),
            self.env.closest_pellet(self.position),
            self.env.distance_to_ghosts(self.position)
        )
        if action is None:
            action = self.best_action()
        self.last_action = action
        # Déplacement de Pac-Man
        new_position, reward = self.env.move(self.position, action)
        self.position = new_position
        self.score += reward
        # Déplacement des fantômes (pour que le nouvel état soit à jour)
        self.env.move_ghosts(self.position, self.last_action)
        new_vision = self.env.get_vision(self.position, vision_size=5)
        new_state = (
            tuple(tuple(row) for row in new_vision),
            self.env.closest_pellet(self.position),
            self.env.distance_to_ghosts(self.position)
        )
        self.qtable.set(current_state, action, reward, new_state)
        return action, reward

    def best_action(self):
        current_vision = self.env.get_vision(self.position, vision_size=5)
        current_state = (
            tuple(tuple(row) for row in current_vision),
            self.env.closest_pellet(self.position),
            self.env.distance_to_ghosts(self.position)
        )
        if random() < self.exploration:
            self.exploration *= self.exploration_decay
            return choice(ACTIONS)
        else:
            return self.qtable.best_action(current_state)

    def __repr__(self):
        return f"{self.position} score:{self.score:.1f} exploration:{self.exploration:.3f}"

