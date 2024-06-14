from db.models import User
from typing import List, Optional, Callable
import random
import math
import json
from copy import deepcopy
import asyncio

ACCELERATION = 1.05


class Paddle:
    def __init__(
        self,
        x,
        y,
        up: bool,
        down: bool,
        speed,
        height,
        half_height,
        width,
        score,
        user: Optional[User],
        channel_name: Optional[str],
        player_id: Optional[int],
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
        self.user: Optional[User] = user
        self.channel_name: Optional[str] = channel_name
        self.player_id: Optional[int] = player_id


class Ball:
    def __init__(self, x, y, dx, dy, speed, radius, temperature=0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.radius = radius


# Predict y of ball when it reaches player2
def get_hit(ball, opp):
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
            old_x - radius > opp.width + opp.x and x - radius <= opp.width + opp.x
        )
        if wentThrough1 and opp_y <= y + radius and y - radius <= opp_y + opp.height:
            ballPosPaddle = (opp_y + opp.half_height) - y
            relPos = ballPosPaddle / (opp.half_height)
            bounceAngle = relPos * maxAngle

            speed = (dx**2 + dy**2) ** 0.5 * ACCELERATION
            dx = speed * math.cos(bounceAngle)
            dy = speed * -math.sin(bounceAngle)

    return y


BIAS = 1


def sigmoid(activation):
    return 1.0 / (1.0 + math.exp(-activation))


def ReLU(activation):
    return max(0, activation)


class Network:
    def __init__(
        self,
        n_inputs: int,
        n_hidden: int,
        n_outputs: int,
        neuron_per_hidden: List[int],
        activation: Callable,
    ) -> None:
        self.layers = []
        self.activation = activation
        self.fitness = float("-inf")
        assert n_hidden == len(neuron_per_hidden)

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

    def serialize(self, path=".", filename="network.json") -> None:
        if not path.endswith("/"):
            path += "/"

        data = {"layers": self.layers}
        with open(path + filename, "w") as out_file:
            json.dump(data, out_file, indent=4)

    @staticmethod
    def deserialize(path) -> "Network":
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
                activation = self.compute(neuron["weights"], inputs)
                neuron["output"] = self.activation(activation)
                new_inputs.append(neuron["output"])
            inputs = new_inputs
        return inputs

    # Backpropagate error and store in neurons
    def backward_propagate(self, expected) -> None:
        # Output layer
        for k, neuron in enumerate(self.layers[-1]):
            output = neuron["output"]
            neuron["delta"] = output * (1.0 - output) * (output - expected[k])

        # Hidden layers
        for i in reversed(range(len(self.layers) - 1)):
            for j, neuron in enumerate(self.layers[i]):
                output = neuron["output"]
                neuron["delta"] = (
                    output
                    * (1.0 - output)
                    * sum(n["delta"] * n["weights"][j] for n in self.layers[i + 1])
                )

    # Update the network's weights
    def update_weights(self, l_rate, _input) -> None:
        # First layer must use input
        for neuron in self.layers[0]:
            for j in range(len(neuron["weights"]) - 1):
                neuron["weights"][j] += -l_rate * neuron["delta"] * _input[j]
            neuron["weights"][-1] += -l_rate * neuron["delta"]  # BIAS weight

        for layer in range(1, len(self.layers)):
            for neuron in self.layers[layer]:
                for j in range(len(neuron["weights"]) - 1):
                    neuron["weights"][j] += (
                        -l_rate * neuron["delta"] * self.layers[layer - 1][j]["output"]
                    )
                neuron["weights"][-1] += -l_rate * neuron["delta"]  # BIAS weight

    # Train the network for a fixed number of epochs
    def train(self, l_rate, n_epoch) -> None:
        best_score = -1
        best_layers = None
        print("Training start")
        epoch = 0
        while epoch < n_epoch:
            print("New training game")
            player1: Paddle = Paddle(
                0.03,
                0.5,
                False,
                False,
                0.016,
                0.166,
                0.083,
                0.0125,
                0,
                None,
                None,
                None,
            )
            bot: Paddle = Paddle(
                1 - 0.03,
                0.5,
                False,
                False,
                0.016,
                0.166,
                0.083,
                0.0125,
                0,
                None,
                None,
                None,
            )
            ball: Ball = Ball(
                0.5,
                0.5,
                0.004,
                0.004,
                0.004,
                0.0128,
            )

            while bot.score < 5 and (best_score == -1 or player1.score < best_score):
                # Update AI if it can be updated
                _input = [ball.x, ball.y, ball.dx, ball.dy, bot.y]
                # AI Move
                (move,) = brain.predict(_input)
                # print(f"AI {move = :.5f}")
                bot.up = move > 2 / 3
                bot.down = move < 1 / 3

                # "Best" move
                hit_y: int = get_hit(ball, player1) if ball.dx > 0 else ball.y
                above: bool = hit_y < bot.y
                on: bool = bot.y < hit_y < bot.y + bot.height
                under: bool = hit_y > bot.y + bot.height

                best = [0.5 if on else 1.0 if above else 0.0]
                # print(best, hit_y, bot.y)
                # Learning while playing
                self.backward_propagate(best)
                self.update_weights(l_rate, _input)

                # update paddle position
                if player1.up and not player1.down:
                    player1.y -= player1.speed
                if player1.down and not player1.up:
                    player1.y += player1.speed
                if player1.y < 0:
                    player1.y = 0
                if player1.y + player1.height > 1:
                    player1.y = 1 - player1.height
                if bot.up and not bot.down:
                    bot.y -= bot.speed
                if bot.down and not bot.up:
                    bot.y += bot.speed
                if bot.y < 0:
                    bot.y = 0
                if bot.y + bot.height > 1:
                    bot.y = 1 - bot.height

                # update ball position
                old_x = ball.x
                ball.x += ball.dx
                ball.y += ball.dy
                if ball.y - ball.radius < 0:
                    ball.y = ball.radius
                    ball.dy *= -1
                elif ball.y + ball.radius > 1:
                    ball.y = 1 - ball.radius
                    ball.dy *= -1

                if ball.x - ball.radius < 0:
                    ball.x = 0.5
                    ball.y = 0.5
                    ball.dx = ball.speed
                    ball.dy = ball.speed
                    player1.y = 0.5
                    bot.y = 0.5
                    bot.score += 1

                elif ball.x + ball.radius > 1:
                    ball.x = 0.5
                    ball.y = 0.5
                    ball.dx = -ball.speed
                    ball.dy = ball.speed
                    player1.y = 0.5
                    bot.y = 0.5
                    player1.score += 1

                player1.y = ball.y - player1.half_height
                # check ball collision with paddles
                maxAngle = math.pi / 4

                wentThrough1 = (
                    old_x - ball.radius > player1.width + player1.x
                    and ball.x - ball.radius <= player1.width + player1.x
                )
                if (
                    wentThrough1
                    and player1.y <= ball.y + ball.radius
                    and ball.y - ball.radius <= player1.y + player1.height
                ):
                    ballPosPaddle = (player1.y + player1.half_height) - ball.y
                    relPos = ballPosPaddle / (player1.half_height)
                    bounceAngle = relPos * maxAngle

                    speed = (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION
                    ball.dx = speed * math.cos(bounceAngle)
                    ball.dy = speed * -math.sin(bounceAngle)

                wentThrough2 = (
                    old_x + ball.radius < bot.x and ball.x + ball.radius >= bot.x
                )
                if (
                    wentThrough2
                    and bot.y <= ball.y + ball.radius
                    and ball.y - ball.radius <= bot.y + bot.height
                ):
                    ballPosPaddle = (bot.y + bot.half_height) - ball.y
                    relPos = ballPosPaddle / (bot.half_height)
                    bounceAngle = relPos * maxAngle

                    speed = (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION
                    ball.dx = speed * -math.cos(bounceAngle)
                    ball.dy = speed * -math.sin(bounceAngle)
            epoch += 1
            print(f"End of training game {epoch} {player1.score = } {bot.score = }")
            if best_score == -1 or player1.score < best_score:
                best_score = player1.score
                best_layers = deepcopy(self.layers)
        self.layers = best_layers
        print("AI Training finished")

    def evaluate(self):
        self.fitness = 0
        player1: Paddle = Paddle(
            0.03,
            0.5,
            False,
            False,
            0.016,
            0.166,
            0.083,
            0.0125,
            0,
            None,
            None,
            None,
        )
        bot: Paddle = Paddle(
            1 - 0.03,
            0.5,
            False,
            False,
            0.016,
            0.166,
            0.083,
            0.0125,
            0,
            None,
            None,
            None,
        )
        ball: Ball = Ball(
            0.5,
            0.5,
            random.uniform(-0.006, 0.006),
            random.uniform(-0.006, 0.006),
            0.004,
            0.0128,
        )

        while player1.score < 5 and bot.score < 5:
            # Update AI if it can be updated
            _input = [ball.x, ball.y, ball.dx, ball.dy, bot.y]
            # AI Move
            (move,) = self.predict(_input)
            # print(f"AI {move = :.5f}")
            bot.up = move > 2 / 3
            bot.down = move < 1 / 3

            # update paddle position
            if player1.up and not player1.down:
                player1.y -= player1.speed
            if player1.down and not player1.up:
                player1.y += player1.speed
            if player1.y < 0:
                player1.y = 0
            if player1.y + player1.height > 1:
                player1.y = 1 - player1.height
            if bot.up and not bot.down:
                # self.fitness += 0.001
                bot.y -= bot.speed
            if bot.down and not bot.up:
                # self.fitness += 0.001
                bot.y += bot.speed
            if bot.y < 0:
                bot.y = 0
            if bot.y + bot.height > 1:
                bot.y = 1 - bot.height

            # update ball position
            old_x = ball.x
            ball.x += ball.dx
            ball.y += ball.dy
            if ball.y - ball.radius < 0:
                ball.y = ball.radius
                ball.dy *= -1
            elif ball.y + ball.radius > 1:
                ball.y = 1 - ball.radius
                ball.dy *= -1

            if ball.x - ball.radius < 0:
                ball.x = 0.5
                ball.y = 0.5
                ball.dx = ball.speed
                ball.dy = ball.speed
                player1.y = 0.5
                bot.y = 0.5
                bot.score += 1

            elif ball.x + ball.radius > 1:
                ball.x = 0.5
                ball.y = 0.5
                ball.dx = -ball.speed
                ball.dy = ball.speed
                player1.y = 0.5
                bot.y = 0.5
                player1.score += 1
            jsp = player1.half_height / 4
            player1.y = ball.y - player1.half_height + random.uniform(-jsp, jsp)
            # check ball collision with paddles
            maxAngle = math.pi / 4

            wentThrough1 = (
                old_x - ball.radius > player1.width + player1.x
                and ball.x - ball.radius <= player1.width + player1.x
            )
            if (
                wentThrough1
                and player1.y <= ball.y + ball.radius
                and ball.y - ball.radius <= player1.y + player1.height
            ):
                ballPosPaddle = (player1.y + player1.half_height) - ball.y
                relPos = ballPosPaddle / (player1.half_height)
                bounceAngle = relPos * maxAngle

                speed = (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION
                ball.dx = speed * math.cos(bounceAngle)
                ball.dy = speed * -math.sin(bounceAngle)

            wentThrough2 = old_x + ball.radius < bot.x and ball.x + ball.radius >= bot.x
            if (
                wentThrough2
                and bot.y <= ball.y + ball.radius
                and ball.y - ball.radius <= bot.y + bot.height
            ):
                self.fitness += 1.0
                ballPosPaddle = (bot.y + bot.half_height) - ball.y
                relPos = ballPosPaddle / (bot.half_height)
                bounceAngle = relPos * maxAngle

                speed = (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION
                ball.dx = speed * -math.cos(bounceAngle)
                ball.dy = speed * -math.sin(bounceAngle)

        self.fitness += bot.score - player1.score

    def predict(self, data) -> List[float]:
        outputs = self.forward_propagate(data)
        return outputs


def child(parents, old_fit):
    a, b = random.sample(parents, 2)
    c = Network(5, 0, 1, [], sigmoid)
    c.layers = []
    for la, lb in zip(a.layers, b.layers):
        clayers = []
        for na, nb in zip(la, lb):
            nc = {
                "weights": [
                    (wa + wb) / 2 for wa, wb in zip(na["weights"], nb["weights"])
                ]
            }
            clayers.append(nc)
        c.layers.append(clayers)
    mutate(c, 0.8)
    return c


def mutate(individual: Network, mutation_rate=0.3):
    for layer in individual.layers:
        for neuron in layer:
            for i, w in enumerate(neuron["weights"]):
                if random.random() < mutation_rate:
                    neuron["weights"][i] += random.uniform(
                        -mutation_rate, mutation_rate
                    )


def natural_selection(n_individuals, generations):
    old_pop = []
    population = [Network(5, 0, 1, [], sigmoid) for _ in range(n_individuals)]
    for generation in range(generations):
        for individual in population:
            individual.evaluate()
        population.sort(key=lambda x: x.fitness)
        best_score = population[-1].fitness
        print(" ".join(f"{x.fitness:.3f}" for x in population))
        print(f"Generation {generation + 1 : 3d} {best_score = :.3f}")
        # if best_score == -5.0:
        #     old_pop = population
        #     population = [Network(5, 0, 1, [], sigmoid) for _ in range(n_individuals)]
        # else:
        bests = 10
        parents = population[-bests:]
        old_pop = population
        population = [
            child(parents, best_score) for _ in range(n_individuals - bests)
        ] + parents
        population = [
            child(parents, best_score) for _ in range(n_individuals - bests)
        ] + parents

    assert old_pop
    print("Training successfully ended")
    return old_pop[-1]


brain = natural_selection(120, 100)
