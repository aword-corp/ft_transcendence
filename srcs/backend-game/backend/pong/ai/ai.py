from db.models import User
from typing import List
import random
import math
import sys


class Paddle:
    def __init__(
        self, x, y, up: bool, down: bool, speed, height, half_height, width, score, user: User
    ):
        self.x = x
        self.y = y
        self.up: bool = up
        self.down: bool = down
        self.speed = speed
        self.height = height
        self.half_height = half_height
        self.width = width
        self.score = score
        self.user: User = user


class Ball:
    def __init__(self, x, y, dx, dy, speed, radius, temperature=0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.radius = radius

perr = lambda x, *args, **kwargs: print(x, *args, **kwargs, file = sys.stderr)
BIAS = 1

# Calculate neuron activation for an input
def compute(weights, _input):
    activation = 0
    for i, weight in zip(_input + [BIAS], weights):
        activation += i * weight
    return activation

def sigmoid(activation):
    return 1.0 / (1.0 + math.exp(-activation))

class Network:
    def __init__(self, n_inputs: int, n_hidden: int, n_outputs: int, neuron_per_hidden: List[int], activation) -> None:
        self.layers = []
        self.activation = activation
        x = 0

        for layer in range(n_hidden):
            hidden_layer = []
            n = n_inputs
            if layer:
                n = neuron_per_hidden[layer - 1]
            for _ in range(neuron_per_hidden[layer]):
                weights = []
                for _ in range(n + 1):
                    weights.append(random.random())
                    x += 1
                hidden_layer.append({"weights": weights})
            self.layers.append(hidden_layer)

        output_layer = []
        n = n_inputs
        if n_hidden:
            n = neuron_per_hidden[n_hidden - 1]
        for _ in range(n_outputs):
            weights = []
            for _ in range(n + 1):
                weights.append(random.random())
                x += 1
            output_layer.append({"weights": weights})
        self.layers.append(output_layer)

    # Forward propagate input to the network output
    def forward_propagate(self, inputs: List[int]) -> List[int]:
        for layer in self.layers:
            new_inputs = []
            for neuron in layer:
                activation = compute(neuron['weights'], inputs)
                neuron['output'] = self.activation(activation)
                new_inputs.append(neuron['output'])
            inputs = new_inputs
        return inputs

    # Backpropagate error and store in neurons
    def backward_propagate(self, expected: List[int]) -> None:
        # Output layer
        for k, neuron in enumerate(self.layers[-1]):
            output = neuron['output']
            neuron['delta'] = output * (1.0 - output) * (output - expected[k])

        # Hidden layers
        for i in reversed(range(len(self.layers) - 1)):
            for j, neuron in enumerate(self.layers[i]):
                output = neuron['output']
                neuron['delta'] = output * (1.0 - output) * sum(n['delta'] * n['weights'][j] for n in self.layers[i + 1])

    # Update the network's weights
    def update_weights(self, l_rate, _input):
        # First layer must use input
        for neuron in self.layers[0]:
            for j in range(len(neuron['weights']) - 1):
                neuron['weights'][j] += -l_rate * neuron['delta'] * _input[j]
            neuron['weights'][-1] += -l_rate * neuron['delta'] # BIAS weight
        
        for layer in range(1, len(self.layers)):
            for neuron in self.layers[layer]:
                for j in range(len(neuron['weights']) - 1):
                    neuron['weights'][j] += -l_rate * neuron['delta'] * self.layers[layer - 1][j]['output']
                neuron['weights'][-1] += -l_rate * neuron['delta'] # BIAS weight

    # Train the network for a fixed number of epochs
    def train(self, train, l_rate, n_epoch):
        for epoch in range(n_epoch):
            sum_error = 0
            for _input, expected in train:
                outputs = self.forward_propagate(_input)
                sum_error += sum((e - o) ** 2 for e, o in zip(expected, outputs))
                self.backward_propagate(expected)
                self.update_weights(l_rate, _input)
            perr(f">epoch={str(epoch).zfill(len(str(n_epoch)))}, error={sum_error:.3f}")
            # if sum_error < 2.6:
            #     break

    def predict(self, data: List[int]) -> List[int]:
        outputs = self.forward_propagate(data)
        return outputs


network = Network(5, 0, 2, [], sigmoid)

