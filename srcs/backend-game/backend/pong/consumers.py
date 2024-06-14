import json
from typing import List, Optional

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from db.models import Count, Elo, Game, User, Tournament
from math import pi, cos, sin
import asyncio
import uuid
from datetime import datetime, timedelta
from .ai.ai import Paddle, Ball, brain, ACCELERATION
import math
import time
import random
from django.core.cache import cache

# from colorama import Fore, Back, Style


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
    games = {}

    users = {}

    async def connect(self):
        await self.accept()
        if self.scope["user"].is_authenticated:
            self.user: User = await User.objects.aget(id=self.scope["user"].id)
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()
            return

        if self.user.id in self.users:
            await self.send(json.dumps({"error": "You are already in a game."}))
            await self.close()
            return

        self.game_id = self.scope["url_route"]["kwargs"]["id"]
        self.game_channel = str(self.game_id).replace("-", "_")
        try:
            self.game: Game = await Game.get_game(self.game_id)
        except Game.DoesNotExist:
            await self.send(json.dumps({"error": "Game does not exist."}))
            await self.close()
            return

        if not await self.game.user_is_in_game(self.user):
            if self.user.is_spectating:
                await self.send(
                    json.dumps({"error": "You are already spectating a game."})
                )
                await self.close()
                return

            self.user.is_spectating = True
            await self.user.asave()

        if self.game.state == self.game.State.ENDED:
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

        if self.game_id not in self.games:
            self.game.state = Game.State.STARTING
            await self.game.asave()
            self.games[self.game_id] = {
                "ball": Ball(
                    0.5,
                    0.5,
                    0.004 * self.game.ball_speed,
                    0.004 * self.game.ball_speed,
                    0.004 * self.game.ball_speed,
                    0.0128 * self.game.ball_size,
                ),
                "started": False,
                "users": [],
                "player_id": 1,
            }

        try:
            if self.user.id not in self.games[
                self.game_id
            ] and await self.game.users.aget(id=self.user.id):
                self.games[self.game_id][self.user.id] = Paddle(
                    0.03 if len(self.games[self.game_id]["users"]) == 0 else 0.97,
                    0.5,
                    False,
                    False,
                    0.016 * self.game.paddle_speed,
                    0.166 * self.game.paddle_size,
                    0.083 * self.game.paddle_size,
                    0.0125 * self.game.paddle_size,
                    0,
                    self.user,
                    self.channel_name,
                    self.games[self.game_id]["player_id"],
                )
                self.games[self.game_id]["users"].append(self.user)
                self.games[self.game_id]["player_id"] += 1
                self.users[self.user.id] = self.user.id

            if self.user.id in self.games[self.game_id]:
                self.user.is_playing = True
                await self.user.asave()
                await self.send(
                    json.dumps(
                        {
                            "type": "broadcast.player.id",
                            "player_id": self.games[self.game_id][
                                self.user.id
                            ].player_id,
                            "user_id": self.user.id,
                        }
                    )
                )

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
        try:
            await self.user.arefresh_from_db()
            if self.user.id in self.users:
                del self.users[self.user.id]
            if self.user.is_spectating:
                self.user.is_spectating = False
                await self.user.asave()
            await self.channel_layer.group_discard(self.game_channel, self.channel_name)
        except AttributeError:
            pass

    async def receive(self, text_data):
        data = json.loads(text_data)

        if "action" in data and self.user.id in self.games[self.game_id]:
            action = data["action"]
            if action == "UP_PRESS_KEYDOWN":
                self.games[self.game_id][self.user.id].up = True
            elif action == "DOWN_PRESS_KEYDOWN":
                self.games[self.game_id][self.user.id].down = True
            elif action == "UP_PRESS_KEYUP":
                self.games[self.game_id][self.user.id].up = False
            elif action == "DOWN_PRESS_KEYUP":
                self.games[self.game_id][self.user.id].down = False
            else:
                await self.send(text_data="Invalid move")

        if "message" in data:
            message = data["message"]
            if isinstance(message, str) and len(message) > 0:
                await self.channel_layer.group_send(
                    self.game_channel,
                    {
                        "type": "broadcast.message",
                        "message": {
                            "user": {
                                "id": self.user.id,
                                "name": self.user.username,
                                "avatar_url": self.user.avatar_url.url
                                if self.user.avatar_url
                                else None,
                                "display_name": self.user.display_name,
                                "grade": self.user.grade,
                                "verified": self.user.verified,
                            },
                            "message": message,
                            "is_player": self.user.id in self.games[self.game_id],
                        },
                    },
                )

        if "offer" in data and self.user.id in self.games[self.game_id]:
            offer = data["offer"]
            await self.channel_layer.group_send(
                self.game_channel,
                {
                    "type": "broadcast.offer",
                    "offer": offer,
                    "user_id": self.user.id,
                },
            )

        if "answer" in data and self.user.id in self.games[self.game_id]:
            answer = data["answer"]
            await self.channel_layer.group_send(
                self.game_channel,
                {
                    "type": "broadcast.answer",
                    "answer": answer,
                    "user_id": self.user.id,
                },
            )

        if "iceCandidate" in data and self.user.id in self.games[self.game_id]:
            iceCandidate = data["iceCandidate"]
            await self.channel_layer.group_send(
                self.game_channel,
                {
                    "type": "broadcast.iceCandidate",
                    "iceCandidate": iceCandidate,
                    "user_id": self.user.id,
                },
            )

    async def game_loop(self, game_id):
        player1: Paddle = self.games[game_id][self.games[game_id]["users"][0].id]
        player2: Paddle = self.games[game_id][self.games[game_id]["users"][1].id]
        ball = self.games[game_id]["ball"]
        await asyncio.sleep(3)
        await self.game.arefresh_from_db()
        self.game.state = Game.State.PLAYING
        await self.game.asave()
        while player1.score < 3 and player2.score < 3:
            wait = False
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
                ball.dx = ball.speed
                ball.dy = ball.speed
                player1.y = 0.5
                player2.y = 0.5
                player2.score += 1
                wait = True if player2.score < 3 else False
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
                wait = True if player1.score < 3 else False
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
                ballPosPaddle = (player1.y + player1.half_height) - ball.y
                relPos = ballPosPaddle / (player1.half_height)
                bounceAngle = relPos * maxAngle

                speed = (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION
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
                ballPosPaddle = (player2.y + player2.half_height) - ball.y
                relPos = ballPosPaddle / (player2.half_height)
                bounceAngle = relPos * maxAngle

                speed = (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION
                ball.dx = speed * -cos(bounceAngle)
                ball.dy = speed * -sin(bounceAngle)

            # sending the new positions to all clients in the game
            await self.channel_layer.group_send(
                self.game_channel,
                {
                    "type": "broadcast.pos",
                    "position": {
                        "ball": {
                            "x": ball.x,
                            "y": ball.y,
                            "radius": ball.radius,
                            "dx": ball.dx,
                            "dy": ball.dy,
                        },
                        "player1": {
                            "x": player1.x,
                            "y": player1.y,
                            "width": player1.width,
                            "height": player1.height,
                            "score": player1.score,
                            "name": player1.user.username,
                        },
                        "player2": {
                            "x": player2.x,
                            "y": player2.y,
                            "width": player2.width,
                            "height": player2.height,
                            "score": player2.score,
                            "name": player2.user.username,
                        },
                    },
                },
            )
            await asyncio.sleep(3 if wait else 0.016)
        await player1.user.arefresh_from_db()
        await player2.user.arefresh_from_db()
        await self.game.arefresh_from_db()
        if player1.score > player2.score and self.game.game_type == Game.Type.MM:
            diff = player2.user.elo - player1.user.elo

            diff_divided = diff / 400

            expected = 1 / (1 + 10**diff_divided)

            self.game.winner = player1.user
            self.game.score_winner = player1.score

            await player1.user.elo_history.acreate(elo=player1.user.elo)

            self.game.elo_winner = player1.user.elo

            player1.user.elo += 20 * (1 - expected)

            self.game.loser = player2.user
            self.game.score_loser = player2.score

            await player2.user.elo_history.acreate(elo=player2.user.elo)

            self.game.elo_loser = player2.user.elo

            player2.user.elo += 20 * (0 - expected)
        elif player1.score < player2.score and self.game.game_type == Game.Type.MM:
            diff = player2.user.elo - player1.user.elo

            diff_divided = diff / 400

            expected = 1 / (1 + 10**diff_divided)

            self.game.loser = player1.user
            self.game.score_loser = player1.score

            await player1.user.elo_history.acreate(elo=player1.user.elo)

            self.game.elo_loser = player1.user.elo

            player1.user.elo += 20 * (0 - expected)

            self.game.winner = player2.user
            self.game.score_winner = player2.score

            await player2.user.elo_history.acreate(elo=player2.user.elo)

            self.game.elo_winner = player2.user.elo

            player2.user.elo += 20 * (1 - expected)
        if self.game.game_type == Game.Type.DUEL:
            await player1.user.duels.aremove(player2.user)
        player1.user.is_playing = False
        player2.user.is_playing = False
        await player1.user.asave()
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

        if await User.is_blocked(self.user.id, message["user"]["id"]):
            return

        if await User.is_blocked(message["user"]["id"], self.user.id):
            return

        await self.send(
            text_data=json.dumps({"type": "broadcast.message", "message": message})
        )

    async def broadcast_offer(self, event):
        if await User.is_blocked(self.user.id, event["user_id"]):
            await self.send(text_data=json.dumps({"error": "You are blocked."}))

        if await User.is_blocked(event["user_id"], self.user.id):
            await self.send(text_data=json.dumps({"error": "You are blocked."}))

        if event["user_id"] == self.user.id:
            return

        await self.send(text_data=json.dumps(event))

    async def broadcast_answer(self, event):
        if await User.is_blocked(self.user.id, event["user_id"]):
            await self.send(text_data=json.dumps({"error": "You are blocked."}))

        if await User.is_blocked(event["user_id"], self.user.id):
            await self.send(text_data=json.dumps({"error": "You are blocked."}))

        if event["user_id"] == self.user.id:
            return

        await self.send(text_data=json.dumps(event))

    async def broadcast_iceCandidate(self, event):
        if await User.is_blocked(self.user.id, event["user_id"]):
            await self.send(text_data=json.dumps({"error": "You are blocked."}))

        if await User.is_blocked(event["user_id"], self.user.id):
            await self.send(text_data=json.dumps({"error": "You are blocked."}))

        if event["user_id"] == self.user.id:
            return

        await self.send(text_data=json.dumps(event))

    async def broadcast_player_id(self, event):
        player_id = event["player_id"]

        await self.send(
            text_data=json.dumps(
                {"type": "broadcast.player_id", "player_id": player_id}
            )
        )

    async def discard_everyone(self, event):
        await self.send(text_data=json.dumps({"details": "Connection closed."}))

        await self.close()

def rand_moment(speed):
	angle = random.uniform(0.5, 1.5 * math.pi)
	dx = speed * math.cos(angle)
	dy = speed * math.sin(angle)
	return dx, dy

class PongAIConsumer(AsyncWebsocketConsumer):
    games = {}

    async def connect(self):
        await self.accept()
        self.task = None
        if self.scope["user"].is_authenticated:
            self.user: User = await User.objects.aget(id=self.scope["user"].id)
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()
            return

        if not brain:
            await self.send(json.dumps({"error": "AI is not ready."}))
            await self.close()
            return
    
        # if self.user.id not in self.games or self.games[self.user.id]["state"] == 2:
        self.games[self.user.id] = {
            "ball": Ball(
                0.5,
                0.5,
                *rand_moment(0.008),
                0.008,
                0.0128,
            ),
            "state": 0,
        }

        self.games[self.user.id][self.user.id] = Paddle(
            0.03,
            0.5,
            False,
            False,
            0.016,
            0.166,
            0.083,
            0.0125,
            0,
            self.user,
            None,
            None,
        )

        self.games[self.user.id]["bot"] = Paddle(
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

        self.task = asyncio.create_task(self.game_loop())

    async def disconnect(self, close_code):
        if self.task:
            self.task.cancel()

    async def receive(self, text_data):
        data = json.loads(text_data)

        if "action" in data and self.user.id in self.games[self.user.id]:
            action = data["action"]
            if action == "UP_PRESS_KEYDOWN":
                self.games[self.user.id][self.user.id].up = True
            elif action == "DOWN_PRESS_KEYDOWN":
                self.games[self.user.id][self.user.id].down = True
            elif action == "UP_PRESS_KEYUP":
                self.games[self.user.id][self.user.id].up = False
            elif action == "DOWN_PRESS_KEYUP":
                self.games[self.user.id][self.user.id].down = False
            else:
                await self.send(text_data="Invalid move")

    async def game_loop(self):
        player1: Paddle = self.games[self.user.id][self.user.id]
        player2: Paddle = self.games[self.user.id]["bot"]
        ball: Ball = self.games[self.user.id]["ball"]
        self.games[self.user.id]["state"] = 1

        ai_last_fetch = 0
        MAX_SPEED = 0.3
        ONE_SECOND_NS = 1_000_000_000

        await asyncio.sleep(3)
        while player1.score < 3 and player2.score < 3:
            # Update AI if it can be updated
            now = time.time_ns()
            if now - ai_last_fetch >= ONE_SECOND_NS / 100:
                # AI Move
                output = brain.activate((player2.y, ball.x, ball.y, ball.dx, ball.dy))
                decision = max(range(len(output)), key = output.__getitem__)
                # decision = random.randint(0, 2) # Random move for tests
                player2.up = decision == 2
                player2.down = decision == 1

                ai_last_fetch = now

            wait = False
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
                wait = True if player2.score < 3 else False
                await self.send(
                    json.dumps(
                        {
                            "type": "broadcast.score",
                            "score": {
                                "player1": player1.score,
                                "player2": player2.score,
                            },
                        }
                    )
                )
            elif ball.x + ball.radius > 1:
                ball.x = 0.5
                ball.y = 0.5
                ball.dx, ball.dy = rand_moment(ball.speed)
                ball.dx = -ball.dx
                player1.y = 0.5
                player2.y = 0.5
                player1.score += 1
                wait = True if player1.score < 3 else False
                await self.send(
                    json.dumps(
                        {
                            "type": "broadcast.score",
                            "score": {
                                "player1": player1.score,
                                "player2": player2.score,
                            },
                        }
                    )
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
                ballPosPaddle = (player1.y + player1.half_height) - ball.y
                relPos = ballPosPaddle / (player1.half_height)
                bounceAngle = relPos * maxAngle

                speed = min(MAX_SPEED, (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION)
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
                ballPosPaddle = (player2.y + player2.half_height) - ball.y
                relPos = ballPosPaddle / (player2.half_height)
                bounceAngle = relPos * maxAngle

                speed = min(MAX_SPEED, (ball.dx**2 + ball.dy**2) ** 0.5 * ACCELERATION)
                ball.dx = speed * -cos(bounceAngle)
                ball.dy = speed * -sin(bounceAngle)

            # sending the new positions to all clients in the game
            await self.send(
                json.dumps(
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
                                "name": player1.user.username,
                            },
                            "player2": {
                                "x": player2.x,
                                "y": player2.y,
                                "width": player2.width,
                                "height": player2.height,
                                "score": player2.score,
                                "name": None,
                            },
                        },
                    }
                )
            )
            await asyncio.sleep(3 if wait else 0.016)

        self.games[self.user.id]["state"] = 2
        await self.send(
            json.dumps(
                {
                    "type": "broadcast.result",
                    "result": {"player1": player1.score, "player2": player2.score},
                }
            )
        )

        await self.close()

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


class MatchmakingConsumer(AsyncWebsocketConsumer):
    queue: list[User] = []

    region: str = ""

    elo_range = {}

    elo_range_timer = {}

    has_task = [False]

    async def connect(self):
        print(self.channel_name)
        await self.accept()
        if self.scope["user"].is_authenticated:
            self.user: User = await User.objects.aget(id=self.scope["user"].id)
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()
            return

        usr_channel_name = await cache.aget(
            f"user_{self.user.id}_tournament_channel_name"
        )

        if usr_channel_name:
            await self.send(json.dumps({"error": "You are already in a queue."}))
            await self.close()
            return

        usr_channel_name = await cache.aget(f"user_{self.user.id}_mm_channel_name")

        if usr_channel_name:
            await self.send(json.dumps({"error": "You are already in a queue."}))
            await self.close()
            return

        if self.user.is_playing:
            await self.send(json.dumps({"error": "You are already in a game."}))
            await self.close()
            return

        if self.user.is_spectating:
            await self.send(json.dumps({"error": "You are already spectating a game."}))
            await self.close()
            return

        await cache.aset(f"user_{self.user.id}_mm_channel_name", self.channel_name)

        self.elo_range[self.user.id] = 60
        self.elo_range_timer[self.user.id] = datetime.now()
        self.queue.append(self.user)
        self.region = self.user.region

        if not self.has_task[0]:
            self.has_task[0] = True
            asyncio.create_task(self.matchmaking())

        await self.channel_layer.group_add("matchmaking", self.channel_name)

        await self.channel_layer.group_send(
            "matchmaking", {"type": "update.message", "users": len(self.queue)}
        )

    async def matchmaking(self):
        while True:
            now = datetime.now()
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
                        users.append(
                            (
                                player,
                                await cache.aget(f"user_{player.id}_mm_channel_name"),
                            )
                        )
                        self.queue.remove(player)
                        await self.channel_layer.group_send(
                            "matchmaking",
                            {"type": "update.message", "users": len(self.queue)},
                        )
                    asyncio.create_task(self.start_game(users))
                else:
                    if (now - self.elo_range_timer[player.id]).total_seconds() > 15:
                        self.elo_range[player.id] += 15
                        self.elo_range_timer[player.id] = now
            await asyncio.sleep(5)

    async def start_game(self, users: List[tuple[User, Optional[str]]]):
        await asyncio.sleep(3)
        can_start = True
        channel_names = {}

        for user, chnl in users:
            channel_names[user.id] = await cache.aget(f"user_{user.id}_mm_channel_name")
            if not channel_names[user.id] or channel_names[user.id] != chnl:
                can_start = False

        if not can_start:
            for _ in range(2):
                user, chnl = users.pop()
                if channel_names[user.id] and channel_names[user.id] == chnl:
                    self.queue.append(user)
                    await self.channel_layer.group_send(
                        "matchmaking",
                        {"type": "update.message", "users": len(self.queue)},
                    )
            return

        game = await Game.objects.acreate(
            uuid=uuid.uuid4(),
            region=self.region,
            state=Game.State.WAITING,
            game_type=Game.Type.MM,
        )

        for _ in range(2):
            user, chnl = users.pop()
            await game.users.aadd(user)
            await self.channel_layer.send(
                chnl,
                {"type": "game.start", "game_id": str(game.uuid)},
            )
            await self.channel_layer.group_discard("matchmaking", chnl)
            await user.arefresh_from_db()
            user.is_playing = True
            await cache.adelete(f"user_{user.id}_mm_channel_name")
            await user.asave()
        await game.asave()

    async def disconnect(self, close_code):
        try:
            await self.user.arefresh_from_db()
            usr_channel_name = await cache.aget(f"user_{self.user.id}_mm_channel_name")
            if self.channel_name == usr_channel_name:
                await cache.adelete(f"user_{self.user.id}_mm_channel_name")
                try:
                    self.queue.remove(self.user)
                except ValueError:
                    pass

            await self.channel_layer.group_discard("matchmaking", self.channel_name)

            await self.channel_layer.group_send(
                "matchmaking", {"type": "update.message", "users": len(self.queue)}
            )
        except AttributeError:
            pass

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


class TournamentConsumer(AsyncWebsocketConsumer):
    tournaments = []

    active_tournament = [False]

    queue = []

    @database_sync_to_async
    def create_tournament(self, user, starting_at, ended_at):
        return Tournament.objects.create(
            name="Tournament n" + str(len(Tournament.objects.all())),
            description="Regular Tournament",
            author=user,
            starting_at=starting_at,
            ended_at=ended_at,
            state=Tournament.State.STARTING,
            region=user.region,
        )

    async def connect(self):
        await self.accept()
        if self.scope["user"].is_authenticated:
            self.user: User = await User.objects.aget(id=self.scope["user"].id)
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()
            return

        usr_channel_name = await cache.aget(
            f"user_{self.user.id}_tournament_channel_name"
        )

        if usr_channel_name:
            await self.send(json.dumps({"error": "You are already in a queue."}))
            await self.close()
            return

        usr_channel_name = await cache.aget(f"user_{self.user.id}_mm_channel_name")

        if usr_channel_name:
            await self.send(json.dumps({"error": "You are already in a queue."}))
            await self.close()
            return

        if self.user.is_playing:
            await self.send(json.dumps({"error": "You are already playing."}))
            await self.close()
            return

        if self.user.is_spectating:
            await self.send(json.dumps({"error": "You are spectating a game."}))
            await self.close()
            return

        await cache.aset(
            f"user_{self.user.id}_tournament_channel_name", self.channel_name
        )

        self.queue.append(self.user)

        print(f"Number of users in queue {len(self.queue)}")
        if not self.active_tournament[0]:
            self.active_tournament[0] = True
            print("Tournament task started")
            asyncio.create_task(self.tournament())

        await self.channel_layer.group_add("tournament", self.channel_name)

        # time_in_queue = tournament.starting_at
        await self.channel_layer.group_send(
            "tournament",
            {
                "type": "update.message",
                "users": len(self.queue),
                # "time_left": (time_in_queue - datetime.now()).strftime("%H:%M:%S"),
            },
        )

    async def tournament(self):
        while True:
            while not len(self.queue):
                await asyncio.sleep(1)

            starting_at = datetime.now() + timedelta(seconds=15)
            ended_at = datetime.now() + timedelta(hours=2)

            while len(self.queue) < 32 and datetime.now() < starting_at:
                await asyncio.sleep(1)

            if len(self.queue) < 2:
                self.queue = []
                await self.channel_layer.group_send(
                    "tournament",
                    {"type": "discard.everyone"},
                )
                return

            tournament = await self.create_tournament(
                self.queue[0], starting_at, ended_at
            )
            self.tournaments.append(tournament)

            players = []
            for player in self.queue:
                await tournament.users.aadd(player)
                players.append(player)
            self.queue = []
            tournament.starting_at = datetime.now()
            tournament.state = Tournament.State.PLAYING
            await tournament.asave()

            await self.run_tournament(tournament, players)

    async def run_tournament(self, tournament, players):
        n_rounds = math.ceil(math.log2(len(players)))
        print(f"Number of rounds = {n_rounds}")
        current_round = 0

        while current_round < n_rounds:
            tree = []
            for i in range(0, len(players), 2):
                if i + 1 < len(players):
                    player1 = players[i]
                    player2 = players[i + 1]
                    game = await self.start_game(player1, player2)
                    tree.append(game)
                else:
                    tree.append(players[i])

            players = await self.collect_winners(tree)
            current_round += 1

        tournament.winner = players[0]
        print(f"Winner is {players[0]}")
        tournament.state = Tournament.State.ENDED
        await tournament.asave()
        print("Tournament ended")

    async def start_game(self, player1, player2):
        await asyncio.sleep(2)
        game = await Game.objects.acreate(
            uuid=uuid.uuid4(),
            region=player1.region,
            state=Game.State.WAITING,
            game_type=Game.Type.TOURNAMENT,
        )
        await game.users.aadd(player1)
        await game.users.aadd(player2)
        await game.asave()
        # print(player1)
        # print(player1.channel_name)
        # print(player2)
        # print(player2.channel_name)
        usr_channel_name = await cache.aget(
            f"user_{player1.id}_tournament_channel_name"
        )
        await self.channel_layer.send(
            usr_channel_name,
            {"type": "game.start", "game_id": str(game.uuid)},
        )
        usr_channel_name = await cache.aget(
            f"user_{player2.id}_tournament_channel_name"
        )
        await self.channel_layer.send(
            usr_channel_name,
            {"type": "game.start", "game_id": str(game.uuid)},
        )
        await player1.arefresh_from_db()
        player1.is_playing = True
        await player1.asave()
        await player2.arefresh_from_db()
        player2.is_playing = True
        await player2.asave()

        return game

    async def collect_winners(self, tree):
        winners = []
        for game in tree:
            if isinstance(game, Game):
                winner = await self.wait_game_winner(game)
                winners.append(winner)
            else:
                winners.append(game)
                await self.send(text_data=json.dumps({"type": "game_waiting"}))
        return winners

    async def wait_game_winner(self, game: Game):
        while game.state != Game.State.ENDED:
            await asyncio.sleep(1)
            game = await Game.objects.aget(id=game.id)
        return await game.get_winner()

    async def game_start(self, event):
        game_id = event["game_id"]
        print(event["game_id"])

        await self.send(
            text_data=json.dumps({"type": "game.start", "game_id": game_id})
        )

    async def disconnect(self, close_code):
        try:
            await self.user.arefresh_from_db()
            usr_channel_name = await cache.aget(
                f"user_{self.user.id}_tournament_channel_name"
            )
            if self.channel_name == usr_channel_name:
                await cache.adelete(f"user_{self.user.id}_tournament_channel_name")
                try:
                    self.queue.remove(self.user)
                except ValueError:
                    pass
                await self.channel_layer.group_send(
                    "tournament",
                    {
                        "type": "update.message",
                        "users": len(self.queue),
                        # "time_left": (time_in_queue - datetime.now()).strftime("%H:%M:%S"),
                    },
                )

            await self.channel_layer.group_discard("tournament", self.channel_name)

        except AttributeError:
            pass

    async def update_message(self, event):
        users = event["users"]
        # time_left = event["time_left"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "update.message",
                    "users": users,
                    # "time_left": time_left
                }
            )
        )

    async def discard_everyone(self, event):
        await self.send(text_data=json.dumps({"details": "Connection closed."}))

        await self.close()
