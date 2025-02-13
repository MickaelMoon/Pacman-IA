from Agent import Agent
from Environnement import Environment
from MazeWindow import MazeWindow
import os
import matplotlib.pyplot as plt

from constante import FILE_AGENT, MAZE

###############################################################################
# Main
###############################################################################

if __name__ == "__main__":
    env = Environment(MAZE, start=(1, 1), 
                     ghost_starts=[(15,15), (15, 1), (1, 15), (8, 8)])
    agent = Agent(env, exploration=1.0, exploration_decay=0.99998)
    episode_count = 0
    max_episodes = 10000000  # Set maximum episodes

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
            window.close()  # Use instance method
        episode_count += 1

    window.schedule(update, 1/60)  # Schedule on window instance
    window.run()  # Call run() on the instance

    agent.save(FILE_AGENT)

    plt.plot(agent.history)
    plt.title(f"Score history ({episode_count} episodes)")
    plt.xlabel("Episodes")
    plt.ylabel("Score")
    plt.show()