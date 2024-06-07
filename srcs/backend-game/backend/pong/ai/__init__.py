from db.models import User
from .ai import AiPlayer

class Paddle:
	def __init__(self, x, y, dy, speed, height, width, score, user: User):
		self.x = x
		self.y = y
		self.dy = dy
		self.speed = speed
		self.height = height
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
