from . import Paddle, Ball, Move

class AiPlayer:
	def __init__(self, name: str):
		self.trained = False
		self.name = name
		print(f"New AI created, say hi to {name}!")

	def train(self, iteration: int) -> None:
		raise NotImplementedError()
		print(self.name, "started training!")
		for epoch in range(iteration):
			# Create game
			# Play game
			# Become winner
			pass
		self.trained = True
		print(self.name, "is now trained!")
	
	def get_move(self, paddle: Paddle, ball: Ball) -> Move:
		move = Move.UP
		print(self.name, "plays", Move(move).name)
		return move
