import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from db.models import Count, Game


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
