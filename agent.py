import torch
import random
import numpy as np
from collections import deque
from game import SnakeGameAI, Direction, Point
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001


class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0
        self.gamma = 0.9
        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = Linear_QNet(11, 256, 3)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, game):
        head = game.snake[0]
        left_point = Point(head.x - 20, head.y)
        right_point = Point(head.x + 20, head.y)
        up_point = Point(head.x, head.y - 20)
        down_point = Point(head.x, head.y + 20)

        left_dir = game.direction == Direction.LEFT
        right_dir = game.direction == Direction.RIGHT
        up_dir = game.direction == Direction.UP
        down_dir = game.direction == Direction.DOWN

        state = [

            (right_dir and game.is_collision(right_point)) or
            (left_dir and game.is_collision(left_point)) or
            (up_dir and game.is_collision(up_point)) or
            (down_dir and game.is_collision(down_point)),


            (up_dir and game.is_collision(right_point)) or
            (down_dir and game.is_collision(left_point)) or
            (left_dir and game.is_collision(up_point)) or
            (right_dir and game.is_collision(down_point)),

            (down_dir and game.is_collision(right_point)) or
            (up_dir and game.is_collision(left_point)) or
            (right_dir and game.is_collision(up_point)) or
            (left_dir and game.is_collision(down_point)),


            left_dir,
            right_dir,
            up_dir,
            down_dir,


            game.food.x < game.head.x,
            game.food.x > game.head.x,
            game.food.y < game.head.y,
            game.food.y > game.head.y
        ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):

        self.epsilon = 80 - self.n_games
        final_move = [0, 0, 0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plotscores = []
    plot_meanscores = []
    total_score = 0
    current_record = 0
    agent = Agent()
    game = SnakeGameAI()
    while True:

        state_old = agent.get_state(game)

        final_move = agent.get_action(state_old)

        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        agent.train_short_memory(
            state_old, final_move, reward, state_new, done)

        agent.remember(state_old, final_move, reward, state_new, done)

        if done:

            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > current_record:
                current_record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score,
                  'current_record:', current_record)

            plotscores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_meanscores.append(mean_score)
            plot(plotscores, plot_meanscores)


if __name__ == '__main__':
    train()
