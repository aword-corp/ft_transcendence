import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from pong.models import Count, Chat


class CountConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)("count", self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)("count", self.channel_name)

    def receive(self, text_data):
        count_obj, created = Count.objects.get_or_create(id=1)
        count_obj.clicks += 1
        count_obj.save()
        message = {"count": count_obj.clicks}
        async_to_sync(self.channel_layer.group_send)(
            "count", {"type": "click.message", "message": message}
        )

    def click_message(self, event):
        count_obj, created = Count.objects.get_or_create(id=1)
        message = {"count": count_obj.clicks}
        self.send(text_data=json.dumps({"message": message}))


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)("chat", self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)("chat", self.channel_name)

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        Chat.objects.create(message=message[:512])
        async_to_sync(self.channel_layer.group_send)(
            "chat", {"type": "chat.message", "message": message}
        )

    def chat_message(self, event):
        message = event["message"]
        self.send(text_data=json.dumps({"message": message}))
