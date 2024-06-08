import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from db.models import Count, Game, User
from math import pi, cos, sin
import asyncio
import uuid
import datetime
from .ai.ai import AiPlayer, Paddle, Ball


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
    acceleration = 1.2
    games = {}

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
            winner = self.game.winner
            winner_score = self.game.score_winner
            winner_obj = {
                "username": winner.username,
                "display_name": winner.display_name,
                "score": winner_score,
            }
            loser = self.game.loser
            loser_score = self.game.score_loser
            loser_obj = {
                "username": loser.username,
                "display_name": loser.display_name,
                "score": loser_score,
            }
            settings_obj = {
                "ball": {"speed": self.game.ball_speed, "size": self.game.ball_size},
                "paddle": {
                    "speed": self.game.paddle_speed,
                    "size": self.game.paddle_size,
                },
            }
            await self.send(
                json.dumps(
                    {
                        "result": {"winner": winner_obj, "loser": loser_obj},
                        "date": self.game.date.isoformat(),
                        "settings": settings_obj,
                        "region": self.game.region,
                    }
                )
            )
            await self.close()
            return

        if self.game.state == self.game.State.ENDED:
            await self.send(json.dumps({"error": "Game has already ended."}))
            await self.close()
            return

        if self.game_id not in self.games:
            self.game.state = Game.State.STARTING
            await self.game.asave()
            self.games[self.game_id] = {
                "ball": Ball(
                    0.5,
                    0.5,
                    0.002 * self.game.ball_speed,
                    0.002 * self.game.ball_speed,
                    0.002 * self.game.ball_speed,
                    0.0128 * self.game.ball_size,
                ),
                "started": False,
                "users": [],
            }

        try:
            if self.user.id not in self.games[
                self.game_id
            ] and await self.game.users.aget(id=self.user.id):
                self.games[self.game_id][self.user.id] = Paddle(
                    0.03 if len(self.games[self.game_id]["users"]) == 0 else 0.97,
                    0.5,
                    0,
                    0.008 * self.game.paddle_speed,
                    0.166 * self.game.paddle_size,
                    0.0125 * self.game.paddle_size,
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
                self.games[self.game_id][self.user.id].dy = -self.games[self.game_id][
                    self.user.id
                ].speed
            elif action == "DOWN_PRESS_KEYDOWN":
                self.games[self.game_id][self.user.id].dy = self.games[self.game_id][
                    self.user.id
                ].speed
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

    async def game_loop(self, game_id):
        player1 = self.games[game_id][self.games[game_id]["users"][0].id]
        player2 = self.games[game_id][self.games[game_id]["users"][1].id]
        ball = self.games[game_id]["ball"]
        await asyncio.sleep(3)
        self.game.state = Game.State.PLAYING
        await self.game.asave()
        while player1.score < 5 and player2.score < 5:
            wait = False
            # update paddle position
            player1.y += player1.dy
            if player1.y < 0:
                player1.y = 0
            if player1.y + player1.height > 1:
                player1.y = 1 - player1.height
            player2.y += player2.dy
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
                ball.dx = ball.speed
                ball.dy = ball.speed
                player1.y = 0.5
                player2.y = 0.5
                player2.score += 1
                wait = True if player2.score < 5 else False
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
                ball.dx = -ball.speed
                ball.dy = ball.speed
                player1.y = 0.5
                player2.y = 0.5
                player1.score += 1
                wait = True if player1.score < 5 else False
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
            await asyncio.sleep(3 if wait else 0.0078125)
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

        await self.channel_layer.group_send(
            self.game_channel,
            {"type": "discard.everyone"},
        )

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

    async def discard_everyone(self, event):
        await self.send(text_data=json.dumps({"details": "Connection closed."}))

        await self.close()


# TODO No data save in DB
class PongAIConsumer(AsyncWebsocketConsumer):
    acceleration = 1.2
    games = {}

    async def connect(self):
        await self.accept()
        if self.scope["user"].is_authenticated:
            self.user: User = self.scope["user"]
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()

        if self.user.id not in self.games:
            self.game.state = Game.State.STARTING
            await self.game.asave()
            self.games[self.user.id] = {
                "ball": Ball(
                    0.5,
                    0.5,
                    0.002 * self.game.ball_speed,
                    0.002 * self.game.ball_speed,
                    0.002 * self.game.ball_speed,
                    0.0128 * self.game.ball_size,
                ),
                "started": False,
                "users": [],
            }

        try:
            if self.user.id not in self.games[
                self.user.id
            ] and await self.game.users.aget(id=self.user.id):
                self.games[self.user.id][self.user.id] = Paddle(
                    0.03 if len(self.games[self.user.id]["users"]) == 0 else 0.97,
                    0.5,
                    0,
                    0.008 * self.game.paddle_speed,
                    0.166 * self.game.paddle_size,
                    0.0125 * self.game.paddle_size,
                    0,
                    self.user,
                )
                self.games[self.user.id]["users"].append(self.user)

            if (
                len(self.games[self.user.id]["users"]) == 2
                and not self.games[self.user.id]["started"]
            ):
                self.games[self.user.id]["started"] = True
                asyncio.create_task(self.game_loop(self.user.id))

        except User.DoesNotExist:
            pass

        await self.channel_layer.group_add(self.game_channel, self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.game_channel, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if "action" in data and self.user.id in self.games[self.user.id]:
            action = data["action"]
            if action == "UP_PRESS_KEYDOWN":
                self.games[self.user.id][self.user.id].dy = -self.games[self.user.id][
                    self.user.id
                ].speed
            elif action == "DOWN_PRESS_KEYDOWN":
                self.games[self.user.id][self.user.id].dy = self.games[self.user.id][
                    self.user.id
                ].speed
            elif action == "UP_PRESS_KEYUP":
                self.games[self.user.id][self.user.id].dy = 0
            elif action == "DOWN_PRESS_KEYUP":
                self.games[self.user.id][self.user.id].dy = 0
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

    async def game_loop(self, user_id):
        player1: Paddle = self.games[user_id][self.games[user_id]["users"][0].id]
        player2 = AiPlayer(
            "AI",
            0.03 if len(self.games[self.user.id]["users"]) == 0 else 0.97,
            0.5,
            0,
            0.008 * self.game.paddle_speed,
            0.166 * self.game.paddle_size,
            0.0125 * self.game.paddle_size,
            0,
        )

        ball: Ball = self.games[user_id]["ball"]

        await asyncio.sleep(3)

        self.game.state = Game.State.PLAYING
        await self.game.asave()
        while player1.score < 5 and player2.score < 5:
            wait = False
            # update paddle position
            player1.y += player1.dy
            if player1.y < 0:
                player1.y = 0
            if player1.y + player1.height > 1:
                player1.y = 1 - player1.height
            player2.y += player2.dy
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
                ball.dx = ball.speed
                ball.dy = ball.speed
                player1.y = 0.5
                player2.y = 0.5
                player2.score += 1
                wait = True if player2.score < 5 else False
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
                ball.dx = -ball.speed
                ball.dy = ball.speed
                player1.y = 0.5
                player2.y = 0.5
                player1.score += 1
                wait = True if player1.score < 5 else False
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
            await asyncio.sleep(3 if wait else 0.0078125)

        player1.user.status = User.Status.ON
        await player1.user.asave()
        self.game.state = self.game.State.ENDED

        del self.games[user_id]

        await self.game.asave()

        await self.channel_layer.group_send(
            self.game_channel,
            {
                "type": "broadcast.result",
                "result": {"player1": player1.score, "player2": player2.score},
            },
        )

        await asyncio.sleep(300)

        await self.channel_layer.group_send(
            self.game_channel,
            {"type": "discard.everyone"},
        )

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

    async def discard_everyone(self, event):
        await self.send(text_data=json.dumps({"details": "Connection closed."}))

        await self.close()


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
        while len(self.queue) > 0:
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
                    if (now - self.elo_range_timer[player.id]).total_seconds() > 15:
                        self.elo_range[player.id] += 15
                        self.elo_range_timer[player.id] = now
            await asyncio.sleep(1)

    async def start_game(self, users):
        await asyncio.sleep(3)
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
