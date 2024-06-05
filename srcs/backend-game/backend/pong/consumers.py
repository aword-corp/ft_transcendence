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

        await self.send(json.dumps({"error": "Invalid route."}))

        await self.close()

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
        def __init__(self, x, y, dy, height, width, score, user: User):
            self.x = x
            self.y = y
            self.dy = dy
            self.height = height
            self.width = width
            self.score = score
            self.user = user

    class Ball:
        def __init__(self, x, y, dx, dy, radius, temperature=0):
            self.x = x
            self.y = y
            self.dx = dx
            self.dy = dy
            self.radius = radius

    acceleration = 1.05
    games = {}

    # update_lock = asyncio.Lock()

    async def connect(self):
        await self.accept()
        if self.scope["user"].is_authenticated:
            self.user: User = self.scope["user"]
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()

        self.game_id = self.scope["url_route"]["kwargs"]["id"]
        self.game_channel = str(self.game_id).replace("-", "_")
        try:
            self.game: Game = await Game.get_game(self.game_id)
        except Game.DoesNotExist:
            await self.send(json.dumps({"error": "Game does not exist."}))
            await self.close()
            return

        if self.game.state == self.game.State.ENDED:
            await self.send(json.dumps({"error": "Game has already ended."}))
            await self.close()
            return

        # async with self.update_lock:
        if self.game_id not in self.games:
            self.game.state = Game.State.STARTING
            await self.game.asave()
            self.games[self.game_id] = {
                "ball": self.Ball(0.5, 0.5, 0.002, -0.002, 0.0128),
                "started": False,
                "users": [],
            }

        try:
            if self.user.id not in self.games[
                self.game_id
            ] and await self.game.users.aget(id=self.user.id):
                self.games[self.game_id][self.user.id] = self.Paddle(
                    0.03 if len(self.games[self.game_id]["users"]) == 0 else 0.97,
                    0.5,
                    0,
                    0.166,
                    0.0125,
                    0,
                    self.user,
                )
                self.games[self.game_id]["users"].append(self.user)

            if (
                len(self.games[self.game_id]["users"]) == 2
                and not self.games[self.game_id]["started"]
            ):
                self.games[self.game_id]["started"] = True
                asyncio.create_task(self.game_loop(self.game_id))

        except User.DoesNotExist:
            pass

        await self.channel_layer.group_add(self.game_channel, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_channel, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if "action" in data and self.user.id in self.games[self.game_id]:
            action = data["action"]
            if action == "UP_PRESS_KEYDOWN":
                self.games[self.game_id][self.user.id].dy = -0.008
            elif action == "DOWN_PRESS_KEYDOWN":
                self.games[self.game_id][self.user.id].dy = 0.008
            elif action == "UP_PRESS_KEYUP":
                self.games[self.game_id][self.user.id].dy = 0
            elif action == "DOWN_PRESS_KEYUP":
                self.games[self.game_id][self.user.id].dy = 0
            else:
                await self.send(text_data="Invalid move")

        if "message" in data:
            message = data["message"]
            await self.channel_layer.group_send(
                self.game_channel,
                {
                    "type": "broadcast.message",
                    "message": {
                        "user": self.user.display_name
                        if self.user.display_name
                        else self.user.username,
                        "message": message,
                    },
                },
            )

    # async def broadcast_pos(self, event):
    #     await self.send(text_data=json.dumps(event))

    # utils

    async def game_loop(self, game_id):
        player1 = self.games[game_id][self.games[game_id]["users"][0].id]
        player2 = self.games[game_id][self.games[game_id]["users"][1].id]
        ball = self.games[game_id]["ball"]
        self.game.state = Game.State.PLAYING
        await self.game.asave()
        while player1.score < 5 and player2.score < 5:
            # async with self.update_lock:
            # update paddle position
            player1.y += player1.dy
            if player1.y < 0:
                player1.y = 0
            if player1.y + player1.height > 1:
                player1.y = 1
            player2.y += player2.dy
            if player2.y < 0:
                player2.y = 0
            if player2.y + player2.height > 1:
                player2.y = 1
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
                ball.dx = 0.002
                ball.dy = 0.002
                player1.y = 0.5
                player2.y = 0.5
                player2.score += 1
                await self.channel_layer.group_send(
                    self.game_channel,
                    {
                        "type": "broadcast.score",
                        "score": {"player1": player1.score, "player2": player2.score},
                    },
                )
            elif ball.x + ball.radius > 1:
                ball.x = 0.5
                ball.y = 0.5
                ball.dx = 0.002
                ball.dy = -0.002
                player1.y = 0.5
                player2.y = 0.5
                player1.score += 1
                await self.channel_layer.group_send(
                    self.game_channel,
                    {
                        "type": "broadcast.score",
                        "score": {"player1": player1.score, "player2": player2.score},
                    },
                )
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
                # ball.temperature += 0.05
                ballPosPaddle = (player1.y + player1.height / 2) - ball.y
                relPos = ballPosPaddle / (player1.height / 2)
                bounceAngle = relPos * maxAngle

                speed = (ball.dx**2 + ball.dy**2) ** 0.5 * self.acceleration
                ball.dx = speed * cos(bounceAngle)
                ball.dy = speed * -sin(bounceAngle)

            wentThrough2 = (
                old_x + ball.radius < player2.x and ball.x + ball.radius >= player2.x
            )
            if (
                wentThrough2
                and player2.y <= ball.y + ball.radius
                and ball.y - ball.radius <= player2.y + player2.height
            ):
                # ball.temperature += 0.05
                ballPosPaddle = (player2.y + player2.height / 2) - ball.y
                relPos = ballPosPaddle / (player2.height / 2)
                bounceAngle = relPos * maxAngle

                speed = (ball.dx**2 + ball.dy**2) ** 0.5 * self.acceleration
                ball.dx = speed * -cos(bounceAngle)
                ball.dy = speed * -sin(bounceAngle)

            # sending the new positions to all clients in the game
            await self.channel_layer.group_send(
                self.game_channel,
                {
                    "type": "broadcast.pos",
                    "position": {
                        "ball": {"x": ball.x, "y": ball.y, "radius": ball.radius},
                        "player1": {
                            "x": player1.x,
                            "y": player1.y,
                            "width": player1.width,
                            "height": player1.height,
                            "score": player1.score,
                        },
                        "player2": {
                            "x": player2.x,
                            "y": player2.y,
                            "width": player2.width,
                            "height": player2.height,
                            "score": player2.score,
                        },
                    },
                },
            )
            await asyncio.sleep(0.0078125)
        if player1.score > player2.score:
            self.game.winner = player1.user
            self.game.loser = player2.user
            self.game.score_winner = player1.score
            self.game.score_loser = player2.score
            expectedA = 1 / (10 ** ((player2.user.elo - player1.user.elo) / 400) + 1)
            changeA = 32 * (1 - expectedA)
            new_elo_A = player1.user.elo + changeA
            player1.user.elo = new_elo_A
            expectedB = 1 / (10 ** ((player1.user.elo - player2.user.elo) / 400) + 1)
            changeB = 32 * (0 - expectedB)
            new_elo_B = player2.user.elo + changeB
            player2.user.elo = new_elo_B
        else:
            self.game.winner = player2.user
            self.game.loser = player1.user
            self.game.score_winner = player2.score
            self.game.score_loser = player1.score
            expectedA = 1 / (10 ** ((player2.user.elo - player1.user.elo) / 400) + 1)
            changeA = 32 * (0 - expectedA)
            new_elo_A = player1.user.elo + changeA
            player1.user.elo = new_elo_A
            expectedB = 1 / (10 ** ((player1.user.elo - player2.user.elo) / 400) + 1)
            changeB = 32 * (1 - expectedB)
            new_elo_B = player2.user.elo + changeB
            player2.user.elo = new_elo_B
        player1.user.status = User.Status.ON
        await player1.user.asave()
        player2.user.status = User.Status.ON
        await player2.user.asave()
        self.game.state = self.game.State.ENDED
        await self.game.asave()

        await self.channel_layer.group_send(
            self.game_channel,
            {
                "type": "broadcast.result",
                "result": {"player1": player1.score, "player2": player2.score},
            },
        )

        await asyncio.sleep(300)

    async def broadcast_pos(self, event):
        position = event["position"]

        await self.send(
            text_data=json.dumps({"type": "broadcast.pos", "position": position})
        )

    async def broadcast_score(self, event):
        score = event["score"]

        await self.send(
            text_data=json.dumps({"type": "broadcast.score", "score": score})
        )

    async def broadcast_result(self, event):
        result = event["result"]

        await self.send(
            text_data=json.dumps({"type": "broadcast.result", "result": result})
        )

    async def broadcast_message(self, event):
        message = event["message"]

        await self.send(
            text_data=json.dumps({"type": "broadcast.message", "message": message})
        )


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        if self.scope["user"].is_authenticated:
            await self.channel_layer.group_add("chat", self.channel_name)
            self.user = self.scope["user"]
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()

        self.game_id = self.scope["url_route"]["kwargs"]["id"]
        try:
            self.game: Game = await Game.get_game(self.game_id)
        except Game.DoesNotExist:
            await self.send(json.dumps({"error": "Game does not exist."}))
            await self.close()
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
        await self.accept()
        if self.scope["user"].is_authenticated:
            self.user: User = self.scope["user"]
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()
            return

        if bool(self.user.channel_name):
            await self.send(json.dumps({"error": "You are already in a queue."}))
            await self.close()
            return

        if self.user.status == User.Status.GAME:
            await self.send(json.dumps({"error": "You are already in a game."}))
            await self.close()
            return

        self.update_lock = asyncio.Lock()

        async with self.update_lock:
            self.elo_range[self.user.id] = 60
            self.elo_range_timer[self.user.id] = datetime.datetime.now()
            self.queue.append(self.user)
            self.region = self.user.region

        if len(self.queue) == 1:
            asyncio.create_task(self.matchmaking())

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
            game = await Game.objects.acreate(
                uuid=uuid.uuid4(), region=self.region, state=Game.State.WAITING
            )
            for _ in range(2):
                user = users.pop()
                await game.users.aadd(user)
                await game.asave()
                await self.channel_layer.send(
                    await user.get_channel_name(),
                    {"type": "game.start", "game_id": str(game.uuid)},
                )
                await self.channel_layer.group_discard(
                    "matchmaking", await user.get_channel_name()
                )
                user.status = User.Status.GAME
                user.channel_name = None
                await user.asave()

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
            text_data=json.dumps({"type": "update.message", "users": repr(users)})
        )
