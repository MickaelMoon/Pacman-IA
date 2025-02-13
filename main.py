###############################################################################
# Main
###############################################################################

import os
import arcade
from matplotlib import pyplot as plt
from Agent import Agent
from Environment import Environment
from MazeWindow import MazeWindow
from constante import FILE_AGENT, MAZE


if __name__ == "__main__":
    env = Environment(MAZE, start=(1, 1), ghost_starts=[(9, 9), (5, 9)]) 
    agent = Agent(env, exploration=0.0, exploration_decay=0.99995)
    episode_count = 0
    max_episodes = 500000  # Set maximum episodes

    if os.path.exists(FILE_AGENT):
        agent.load(FILE_AGENT)

    window = MazeWindow(agent)
    window.setup()

    # Add progress tracking
    def update(dt):
        global episode_count
        if episode_count % 1000 == 0:
            print(f"Episode {episode_count}, Score: {agent.score:.1f}, Exploration: {agent.exploration:.3f}")
        if episode_count >= max_episodes:
            arcade.close_window()
        episode_count += 1

    arcade.schedule(update, 1/60)
    arcade.run()

    agent.save(FILE_AGENT)

    plt.plot(agent.history)
    plt.title(f"Score history ({episode_count} episodes)")
    plt.xlabel("Episodes")
    plt.ylabel("Score")
    plt.show()