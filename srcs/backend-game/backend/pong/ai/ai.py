from typing import Optional
import random
import math
import neat
import os
import pickle

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
		user,
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
		self.hits = 0
		self.moves = 0
		self.user = user
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


def rand_moment(speed):
	angle = random.uniform(0.5, 1.5 * math.pi)
	dx = speed * math.cos(angle)
	dy = speed * math.sin(angle)
	return dx, dy

def sigmoid(x):
	return 1.0 / (1.0 + math.exp(-x))

def train_ai(genome1, genome2, config):
	"""
	Train the AI by passing two NEAT neural networks and the NEAt config object.
	These AI's will play against eachother to determine their fitness.
	"""
	net1 = neat.nn.FeedForwardNetwork.create(genome1, config)
	if genome2:
		net2 = neat.nn.FeedForwardNetwork.create(genome2, config)

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
	player2: Paddle = Paddle(
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
		*rand_moment(0.008),
		0.008,
		0.0128,
	)

	ONE_SECOND_NS = 1_000_000_000
	max_speed = 0.03
	max_hits = 50
	max_ticks = 7000

	ticks = 0
	running = True
	while ticks < max_ticks and running and player1.score + player2.score < 1 and player1.hits < max_hits and player2.hits < max_hits:

		# AI Move
		if ticks % 7 == 0:
			output1 = net1.activate(
				(
					player1.y + player1.half_height,
					player2.y + player2.half_height,
					ball.x, 
					ball.y, 
					ball.dx, 
					ball.dy
				)
			)
			up, down = map(sigmoid, output1)
			player1.up = up > 0.5 and up > down
			player1.down = down > 0.5 and down > up
			player1.moves += player1.up ^ player1.down

		if genome2:
			output2 = net2.activate((player2.y, player1.y, ball.x, ball.y, ball.dx, ball.dy))
			decision2 = max(range(len(output2)), key = output2.__getitem__)
			player2.up = decision2 == 2
			player2.down = decision2 == 1
			player2.moves += player2.up ^ player2.down
		else:
			player2.y = ball.y - player2.half_height

		# update paddle position
		if player1.up and not player1.down:
			player1.y -= player1.speed
		if player1.down and not player1.up:
			player1.y += player1.speed
		if player1.y < 0:
			player1.y = 0
		if player1.y + player1.height > 1:
			player1.y = 1 - player1.height
		if player2.up and not player2.down:
			player2.y -= player2.speed
		if player2.down and not player2.up:
			player2.y += player2.speed
		if player2.y < 0:
			player2.y = 0
		if player2.y + player2.height > 1:
			player2.y = 1 - player2.height
		
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
			ball.dx, ball.dy = rand_moment(ball.speed)
			player1.y = 0.5
			player2.y = 0.5
			player2.score += 1

		elif ball.x + ball.radius > 1:
			ball.x = 0.5
			ball.y = 0.5
			ball.dx, ball.dy = rand_moment(ball.speed)
			ball.dx = -ball.dx
			player1.y = 0.5
			player2.y = 0.5
			player1.score += 1

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
			player1.hits += 1
			ballPosPaddle = (player1.y + player1.half_height) - ball.y
			relPos = ballPosPaddle / (player1.half_height)
			bounceAngle = relPos * maxAngle

			speed = min(max_speed, (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION)
			ball.dx = speed * math.cos(bounceAngle)
			ball.dy = speed * -math.sin(bounceAngle)

		wentThrough2 = (
			old_x + ball.radius < player2.x and ball.x + ball.radius >= player2.x
		)
		if (
			wentThrough2
			and player2.y <= ball.y + ball.radius
			and ball.y - ball.radius <= player2.y + player2.height
		):
			player2.hits += 1
			ballPosPaddle = (player2.y + player2.half_height) - ball.y
			relPos = ballPosPaddle / (player2.half_height)
			bounceAngle = relPos * maxAngle

			speed = min(max_speed, (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION)
			ball.dx = speed * -math.cos(bounceAngle)
			ball.dy = speed * -math.sin(bounceAngle)

		ticks += 1

	genome1.fitness = player1.hits
	if genome2:
		genome2.fitness += player2.hits
	
	return False

def eval_genomes(genomes, config):
	"""
	Run each genome against eachother one time to determine the fitness.
	"""
	n = len(genomes)
	for i in range(n):
		id1, genome1 = genomes[i]
		genome1.fitness = 0
		force_quit = train_ai(genome1, None, config)
		if force_quit:
			quit()
		# continue
		# for j in range(i + 1, n):
		# 	id1, genome1 = genomes[i]
		# 	id2, genome2 = genomes[j]
		# 	genome1.fitness = 0
		# 	genome2.fitness = 0 if genome2.fitness == None else genome2.fitness
		# 	# print(i, "vs", j)
		# 	force_quit = train_ai(genome1, genome2, config)
		# 	if force_quit:
		# 		quit()

def run_neat(config):
	pop = neat.Checkpointer.restore_checkpoint('neat-checkpoint-1606')
	# pop = neat.Population(config)
	pop.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	pop.add_reporter(stats)
	pop.add_reporter(neat.Checkpointer(1))

	winner = pop.run(eval_genomes, 500)
	return winner

local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, 'config.txt')
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
						 neat.DefaultSpeciesSet, neat.DefaultStagnation,
						 config_path)
# Training phase
# best_gen = run_neat(config)
# brain = None
# with open(f'winner_genome.pkl', 'wb') as f:
#     pickle.dump(best_gen, f)
# brain = neat.nn.FeedForwardNetwork.create(best_gen, config)

# Deserealize pre-trained
brain = None
with open('./pong/ai/winner_genome.pkl', 'rb') as f:
    brain = pickle.load(f)
    brain = neat.nn.FeedForwardNetwork.create(brain, config)
