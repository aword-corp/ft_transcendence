import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from db.models import Count, GlobalChat, Game


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
        count_obj = Count.objects.get_or_create(id=1)[0]
        count_obj.clicks += 1
        count_obj.save()
        return count_obj

    async def connect(self):
        await self.channel_layer.group_add("count", self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("count", self.channel_name)

    async def receive(self, text_data):
        count_obj = await self.increment_count()
        message = {"count": count_obj.clicks}

        await self.channel_layer.group_send(
            "count", {"type": "click.message", "message": message}
        )

    async def click_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({"message": message}))


class PongConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        self.game_id = self.scope["url_route"]["kwargs"]["id"]
        self.user = None
        try:
            self.game: Game = await Game.get_game(self.game_id)
        except Game.DoesNotExist:
            self.close(1000, "Game does not exists.")
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
        if self.scope["user"].is_authenticated:
            await self.accept()
            await self.channel_layer.group_add("chat", self.channel_name)
            self.user = self.scope["user"]
        else:
            await self.accept()
            await self.send(text_data=json.dumps({"error": "You need to be logged in."}))
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("chat", self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        if "message" not in text_data_json or not text_data_json["message"]:
            message = "No message found."
            await self.send(text_data=json.dumps({"error": message}))
            return

        message = str(text_data_json["message"])
        await GlobalChat.create_message(self.user, message)
        await self.channel_layer.group_send(
            "chat", {"type": "chat.message", "message": message}
        )

    async def chat_message(self, event):
        message = event["message"]

        await self.send(text_data=json.dumps({"message": message}))
