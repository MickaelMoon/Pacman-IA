###############################################################################
# Fonction utilitaire pour le Q-Learning
###############################################################################

from matplotlib.pylab import choice
from constante import ACTIONS


def arg_max(table):
    """Retourne l'action associée à la valeur maximale dans le dictionnaire."""
    return max(table, key=table.get)

###############################################################################
# QTable : stockage et mise à jour de la Q-table
###############################################################################

class QTable:
    def __init__(self, learning_rate=0.2, discount_factor=0.95):
        self.dic = {}
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor

    def set(self, state, action, reward, new_state):
        if state not in self.dic:
            self.dic[state] = {a: 0 for a in ACTIONS}
        if new_state not in self.dic:
            self.dic[new_state] = {a: 0 for a in ACTIONS}
        old_value = self.dic[state][action]
        max_next = max(self.dic[new_state].values())
        # Formule de mise à jour Q-learning
        delta = reward + self.discount_factor * max_next - old_value
        self.dic[state][action] = old_value + self.learning_rate * delta

    def best_action(self, state):
        if state in self.dic:
            return arg_max(self.dic[state])
        else:
            return choice(ACTIONS)

    def __repr__(self):
        res = ' ' * 11
        for action in ACTIONS:
            res += f'{action:5s}'
        res += '\n'
        for state in self.dic:
            res += str(state) + " "
            for action in self.dic[state]:
                res += f"{self.dic[state][action]:5.1f}"
            res += '\n'
        return res