from db.models import User
from typing import List, Optional, Callable
import random
import math
import sys
import json


class Paddle:
	def __init__(
		self, x, y, up: bool, down: bool, speed, height, half_height, width, score, user: Optional[User]
	):
		self.x = x
		self.y = y
		self.up = up
		self.down = down
		self.speed = speed
		self.height = height
		self.half_height = half_height
		self.width = width
		self.score = score
		self.user = user


class Ball:
	def __init__(self, x, y, dx, dy, speed, radius, temperature=0):
		self.x = x
		self.y = y
		self.dx = dx
		self.dy = dy
		self.speed = speed
		self.radius = radius

# Predict y of ball when it reaches player2
def get_hit(ball, opp, acceleration):
	x = ball.x
	y = ball.y
	dx = ball.dx
	dy = ball.dy
	radius = ball.radius
	speed = ball.speed
	
	while True:
		old_x = x
		x += dx
		y += dy
		if y - radius < 0:
			y = radius
			dy *= -1
		elif y + radius > 1:
			y = 1 - radius
			dy *= -1

		if x - radius < 0:
			break
		elif x + radius > 1:
			break
		# check ball collision with paddles
		maxAngle = math.pi / 4
		opp_y = y
		wentThrough1 = (
			old_x - radius > opp.width + opp.x
			and x - radius <= opp.width + opp.x
		)
		if (
			wentThrough1
			and opp_y <= y + radius
			and y - radius <= opp_y + opp.height
		):
			ballPosPaddle = (opp_y + opp.half_height) - y
			relPos = ballPosPaddle / (opp.half_height)
			bounceAngle = relPos * maxAngle

			speed = (dx**2 + dy**2) ** 0.5 * acceleration
			dx = speed * math.cos(bounceAngle)
			dy = speed * -math.sin(bounceAngle)

	return y

BIAS = 1

def sigmoid(activation):
	return 1.0 / (1.0 + math.exp(-activation))

def ReLU(activation):
	return max(0, activation)

class Network:
	def __init__(self, n_inputs: int, n_hidden: int, n_outputs: int, neuron_per_hidden: List[int], activation: Callable) -> None:
		self.layers = []
		self.activation = activation

		for layer in range(n_hidden):
			hidden_layer = []
			n = n_inputs
			if layer:
				n = neuron_per_hidden[layer - 1]
			for _ in range(neuron_per_hidden[layer]):
				weights = []
				for _ in range(n + 1):
					weights.append(random.random())
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
			output_layer.append({"weights": weights})
		self.layers.append(output_layer)

	def serialize(self, path = ".", filename = "network.json") -> None:
		if not path.endswith('/'):
			path += '/'

		data = {
			"layers": self.layers
		}
		with open(path + filename, "w") as out_file:
			json.dump(data, out_file, indent=4)
	
	@staticmethod
	def deserialize(path) -> 'Network':
		with open(path, "r") as in_file:
			data = json.load(in_file)
			layers = data["layers"]
			activation = sigmoid
			network = Network(0, 0, 0, [], activation)
			network.layers = layers
			return network
	
	# Compute neuron activation for an input
	def compute(self, weights, _input) -> int:
		activation = 0
		for i, weight in zip(_input + [BIAS], weights):
			activation += i * weight
		return activation

	# Forward propagate input to the network output
	def forward_propagate(self, inputs) -> List[float]:
		for layer in self.layers:
			new_inputs = []
			for neuron in layer:
				activation = self.compute(neuron['weights'], inputs)
				neuron['output'] = self.activation(activation)
				new_inputs.append(neuron['output'])
			inputs = new_inputs
		return inputs

	# Backpropagate error and store in neurons
	def backward_propagate(self, expected) -> None:
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
	def update_weights(self, l_rate, _input) -> None:
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
	def train(self, l_rate, n_epoch) -> None:
		print("Training start")
		for epoch in range(n_epoch):
			opp = Network(5, 0, 2, [], sigmoid)
			pass
		

	def predict(self, data) -> List[float]:
		outputs = self.forward_propagate(data)
		return outputs

brain = Network(5, 0, 2, [], sigmoid)
# brain.train(0.5, 100)
