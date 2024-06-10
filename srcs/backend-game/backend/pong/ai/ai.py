from db.models import User


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
