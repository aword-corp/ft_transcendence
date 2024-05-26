import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from db.models import Count, Game, User
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
        await self.channel_layer.group_discard(self.game_id, self.channel_name)

    async def receive(self, text_data):
        if text_data == "UP_PRESS":
            position = {self.user: 0}
        elif text_data == "DOWN_PRESS":
            position = {self.user: 0}
        elif text_data == "UP_RELEASE":
            pass
            #
        elif text_data == "DOWN_RELEASE":
            pass
            # faire une boucle de jeu et bouger le joueur de x distance selon le temps ecoule
        else:
            await self.send(text_data="Invalid move")
            return
        # Update la position du joueur
        # Renvoyer la position du joueur

        await self.channel_layer.group_send(
            self.game_id, {"type": "broadcast.pos", "position": [self.user, position]}
        )

    async def broadcast_pos(self, event):
        user, pos = event["position"]

        await self.send(text_data=json.dumps({"position": pos}))


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

    async def update_message(self, event):
        users = event["users"]

        await self.send(text_data=json.dumps(users))
