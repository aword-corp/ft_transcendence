from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    path("ws/update/", consumers.UpdateConsumer.as_asgi()),
    re_path(
        r"(?P<arg>(.*))", consumers.DefaultConsumer.as_asgi()
    ),  # Regex match any string even empty
]
