from . import Paddle, Ball # TODO Fix import

# dy +- 0.008
class AiPlayer(Paddle):
	def __init__(self, name: str, x, y, dy, speed, height, width, score):
		self.trained = False
		self.name = name
		super().__init__(x, y, dy, speed, height, width, score, None)
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
	
	def update_move(self, paddle: Paddle, ball: Ball) -> None:
		self.dy = -0.008
		print(self.name, "plays", self.dy)

