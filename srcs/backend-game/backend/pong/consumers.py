import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from db.models import Count, Chat


class CountConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def get_count(self):
        return Count.objects.get_or_create(id=1)[0]

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
        count_obj = await self.get_count()
        message = {"count": count_obj.clicks}

        await self.send(text_data=json.dumps({"message": message}))

class ChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def create_message(self, message):
        Chat.objects.create(message=message[:512])

    async def connect(self):
        await self.channel_layer.group_add("chat", self.channel_name)
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("chat", self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        await self.create_message(message)
        await self.channel_layer.group_send(
            "chat", {"type": "chat.message", "message": message}
        )

    async def chat_message(self, event):
        message = event["message"]
        
        await self.send(text_data=json.dumps({"message": message}))
