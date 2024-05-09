import json

from channels.generic.websocket import WebsocketConsumer
from pong.models import Count

class CountConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        count_obj, created = Count.objects.get_or_create(id=1)
        count_obj.clicks += 1
        count_obj.save()
        message = {
            "count": count_obj.clicks
        }

        self.send(text_data=json.dumps({"message": message}))