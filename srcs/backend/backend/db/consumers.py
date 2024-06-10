import json

from channels.generic.websocket import AsyncWebsocketConsumer
from .models import User
from django.core.cache import cache


class DefaultConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        await self.send(json.dumps({"error": "Invalid route."}))

        await self.close()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        pass


class UpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        if self.scope["user"].is_authenticated:
            self.user: User = self.scope["user"]
        else:
            await self.send(json.dumps({"error": "You need to be logged in."}))
            await self.close()

        channel = await cache.aget(f"user_{self.user.id}_channel")

        if not channel:
            channel = []

        channel.append(self.channel_name)

        await cache.aset(f"user_{self.user.id}_channel", channel)

    async def disconnect(self, close_code):
        channel = await cache.aget(f"user_{self.user.id}_channel")
        if not channel:
            return
        try:
            channel.remove(self.channel_name)
            await cache.aset(f"user_{self.user.id}_channel", channel)
        except ValueError:
            pass

    async def receive(self, text_data):
        pass
