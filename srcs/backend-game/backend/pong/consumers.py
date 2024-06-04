import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from db.models import Count, Game, User
from math import pi, cos, sin
import asyncio
import uuid
import datetime


class DefaultConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        await self.close(1000, "Invalid route.")

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        pass


class CountConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def increment_count(self):
        count_obj, created = Count.objects.get_or_create(id=1)
        count_obj.clicks += 1
        count_obj.save()

        return count_obj

    async def connect(self):
        await self.accept()

        await self.channel_layer.group_add("count", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("count", self.channel_name)

    async def receive(self, text_data):
        count_obj = await self.increment_count()
        await self.channel_layer.group_send(
            "count", {"type": "click.message", "count": str(count_obj.clicks)}
        )

    async def click_message(self, event):
        await self.send(text_data=event["count"])


class PongConsumer(AsyncWebsocketConsumer):
    class Paddle:
        def __init__(self, x, y, dy, height, width, score):
            self.x = x
            self.y = y
            self.dy = dy
            self.height = height
            self.width = width
            self.score = score

    class Ball:
        def __init__(self, x, y, dx, dy, radius, temperature=0):
            self.x = x
            self.y = y
            self.radius = radius
            self.dx = dx
            self.dy = dy

    acceleration = 1.05
    games = {}
    game_started = False

    async def connect(self):
        await self.accept()
        if self.scope["user"].is_authenticated:
            self.user = self.scope["user"]
        else:
            await self.close(1000, "You need to be logged in.")

        self.game_id = self.scope["url_route"]["kwargs"]["id"]
        try:
            self.game: Game = await Game.get_game(self.game_id)
        except Game.DoesNotExist:
            await self.close(1000, "Game does not exists.")
            return

        self.update_lock = asyncio.Lock()

        if self.game not in self.games:
            async with self.update_lock:
                self.games[self.game_id] = {
                    "ball": self.Ball(0.5, 0.5, 0.09, -0.05, 0.05),
                    "users": [],
                }

        if len(self.games[self.game_id]["users"]) < 2:
            async with self.update_lock:
                self.games[self.game_id][self.user.id] = self.Paddle(
                    0, 0.5, 0, 0.05, 0.01, 0
                )
                self.games[self.game_id]["users"].append(self.user)
        elif len(self.games[self.game_id]["users"]) == 2 and not self.game_started:
            self.game_started = True
            asyncio.create_task(self.game_loop())

        await self.channel_layer.group_add(self.game_id, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_id, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")
        if action == "UP_PRESS_KEYDOWN":
            self.games[self.game_id][self.user.id].dy = -5
        elif action == "DOWN_PRESS_KEYDOWN":
            self.games[self.game_id][self.user.id].dy = 5
        elif action == "UP_PRESS_KEYUP":
            self.games[self.game_id][self.user.id].dy = 0
        elif action == "DOWN_PRESS_KEYUP":
            self.games[self.game_id][self.user.id].dy = 0
        else:
            await self.send(text_data="Invalid move")

    # async def broadcast_pos(self, event):
    #     await self.send(text_data=json.dumps(event))

    # utils
    def no_winner(self):
        b = True
        for user in self.games[self.game_id]["users"]:
            if self.games[self.game_id][user.id].score >= 3:
                b = False
        return b

    def reset_ball(self, player_n):
        ball = self.games[self.game_id]["ball"]
        ball.x = 0.5
        ball.y = 0.5
        ball.dx *= 0.05 if player_n == 1 else -0.05
        ball.dy *= 0.05

    def reset_paddles(self):
        for user in self.games[self.game_id]["users"]:
            self.games[self.game_id][user.id].y = 0.5

    async def game_loop(self):
        player1 = self.games[self.game_id]["users"][0]
        player2 = self.games[self.game_id]["users"][1]
        while self.no_winner():
            async with self.update_lock:
                # update paddle position
                for user in self.games[self.game_id]["users"]:
                    self.games[self.game_id][user.id].y += self.games[self.game_id][
                        user.id
                    ].dy
                    if self.games[self.game_id][user.id].y < 0:
                        self.games[self.game_id][user.id].y = 0
                    elif (
                        self.games[self.game_id][user.id].y
                        + self.games[self.game_id][user.id].height
                        > 1
                    ):
                        self.games[self.game_id][user.id].y = 1

                # update ball position
                ball = self.games[self.game_id]["ball"]
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
                    self.reset_ball(self, 1)
                    self.reset_paddles()
                    self.games[self.game_id][player2.id].score += 1
                elif ball.x + ball.radius > 1:
                    self.reset_ball(self, 2)
                    self.reset_paddles()
                    self.games[self.game_id][player1.id].score += 1

                # check ball collision with paddles
                maxAngle = pi / 4

                wentThrough1 = (
                    old_x - ball.radius > player1.width + player1.x
                    and ball.x - ball.radius <= player1.width + player1.x
                )
                if (
                    wentThrough1
                    and player1.y <= ball.y + ball.radius
                    and ball.y - ball.radius <= player1.y + player1.height
                ):
                    ball.temperature += 0.05
                    ballPosPaddle = (player1.y + player1.height / 2) - ball.y
                    relPos = ballPosPaddle / (player1.height / 2)
                    bounceAngle = relPos * maxAngle

                    speed = (ball.dx**2 + ball.dy**2) ** 0.5 * self.acceleration
                    ball.dx = speed * cos(bounceAngle)
                    ball.dy = speed * -sin(bounceAngle)

                wentThrough2 = (
                    old_x + ball.radius < player2.x
                    and ball.x + ball.radius >= player2.x
                )
                if (
                    wentThrough2
                    and player2.y <= ball.y + ball.radius
                    and ball.y - ball.radius <= player2.y + player2.height
                ):
                    ball.temperature += 0.05
                    ballPosPaddle = (player2.y + player2.height / 2) - ball.y
                    relPos = ballPosPaddle / (player2.height / 2)
                    bounceAngle = relPos * maxAngle

                    speed = (ball.dx**2 + ball.dy**2) ** 0.5 * self.acceleration
                    ball.dx = speed * -cos(bounceAngle)
                    ball.dy = speed * -sin(bounceAngle)

                # sending the new positions to all clients in the game
                await self.channel_layer.group_send(
                    self.game_id,
                    {
                        "type": "broadcast.pos",
                        "position": [self.user, self.games[self.game_id]],
                    },
                )
                await asyncio.sleep(0.05)

    async def broadcast_pos(self, event):
        position = event["position"]

        await self.send(text_data=json.dumps(position))


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_add("chat", self.channel_name)
            self.user = self.scope["user"]
        else:
            await self.close(1000, "You need to be logged in.")

        self.game_id = self.scope["url_route"]["kwargs"]["id"]
        try:
            self.game: Game = await Game.get_game(self.game_id)
        except Game.DoesNotExist:
            await self.close(1000, "Game does not exists.")
            return

        await self.channel_layer.group_add(self.game_id, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("chat", self.channel_name)

    async def receive(self, text_data):
        await self.channel_layer.group_send(
            "chat", {"type": "chat.message", "message": text_data[:512]}
        )

    async def chat_message(self, event):
        message = event["message"]
        user_id = event["user_id"]
        username = event["username"]

        await self.send(
            text_data=json.dumps(
                {"user_id": user_id, "username": username, "message": message}
            )
        )


class MatchmakingConsumer(AsyncWebsocketConsumer):
    queue: list[User] = []

    region: str = ""

    elo_range = {}

    elo_range_timer = {}

    async def connect(self):
        if self.scope["user"].is_authenticated:
            self.user: User = self.scope["user"]
        else:
            await self.close(1000, "You need to be logged in.")
            return

        if bool(self.user.channel_name):
            await self.close(1000, "You are already in queue.")
            print("test")
            return

        if self.user.status == User.Status.GAME:
            await self.close(1000, "You are already in a game.")
            return

        self.update_lock = asyncio.Lock()

        async with self.update_lock:
            self.elo_range[self.user.id] = 30
            self.elo_range_timer[self.user.id] = datetime.datetime.now()
            self.queue.append(self.user)
            self.region = self.user.region

        if len(self.queue) == 1:
            asyncio.create_task(self.matchmaking())

        await self.accept()

        await self.user.set_channel_name(self.channel_name)

        await self.channel_layer.group_add("matchmaking", self.channel_name)

        await self.channel_layer.group_send(
            "matchmaking", {"type": "update.message", "users": repr(self.queue)}
        )

    async def matchmaking(self):
        while True:
            async with self.update_lock:
                if len(self.queue) == 0:
                    break
                now = datetime.datetime.now()
                for player in self.queue:
                    potential_matches = [
                        opps
                        for opps in self.queue
                        if abs(opps.elo - player.elo) <= self.elo_range[player.id]
                        and abs(opps.elo - player.elo) <= self.elo_range[opps.id]
                    ]

                    if len(potential_matches) >= 2:
                        users = []
                        for _ in range(2):
                            player = potential_matches.pop()
                            users.append(player)
                            self.queue.remove(player)
                            await self.channel_layer.group_send(
                                "matchmaking",
                                {"type": "update.message", "users": repr(self.queue)},
                            )
                            self.elo_range.pop(player.id)
                        asyncio.create_task(self.start_game(users))
                    else:
                        if now.second - self.elo_range_timer[player.id].second > 30:
                            self.elo_range[player.id] *= 1.5
                            self.elo_range_timer[player.id] = now
                await asyncio.sleep(1)

    async def start_game(self, users):
        await asyncio.sleep(3)
        async with self.update_lock:
            game = await Game.objects.acreate(uuid=uuid.uuid4(), region=self.region)
            for _ in range(2):
                user = users.pop()
                await self.channel_layer.group_discard(
                    "matchmaking", await user.get_channel_name()
                )
                await game.users.aadd(user)
                user.status = User.Status.GAME
                await user.asave()
                await self.channel_layer.send(
                    await user.get_channel_name(),
                    {"type": "game.start", "game_id": str(game.uuid)},
                )

    async def disconnect(self, close_code):
        try:
            self.queue.remove(self.user)
        except (ValueError, AttributeError):
            return

        await self.user.set_channel_name(None)

        await self.channel_layer.group_discard("matchmaking", self.channel_name)

        await self.channel_layer.group_send(
            "matchmaking", {"type": "update.message", "users": repr(self.queue)}
        )

    async def game_start(self, event):
        game_id = event["game_id"]
        print(event["game_id"])

        await self.send(
            text_data=json.dumps({"type": "game.start", "game_id": game_id})
        )

    async def update_message(self, event):
        users = event["users"]

        await self.send(
            text_data=json.dumps({"type": "update.message", "users": users})
        )
