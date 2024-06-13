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
            return

        channel = await cache.aget(f"user_{self.user.id}_channel")

        if not channel:
            self.user.is_online = True
            await self.user.asave()
            channel = []
            if not self.user.is_invisible:
                for user in self.user.friends.all():
                    chnls = cache.get(f"user_{user.id}_channel")

                    if chnls:
                        for chnl in chnls:
                            await self.channel_layer.send(
                                chnl,
                                {
                                    "type": "user.connected.sent",
                                    "from": self.user.username,
                                },
                            )

        channel.append(self.channel_name)

        await cache.aset(f"user_{self.user.id}_channel", channel)

    async def disconnect(self, close_code):
        try:
            channel = await cache.aget(f"user_{self.user.id}_channel")
            if not channel:
                return
            channel.remove(self.channel_name)

            if not len(channel):
                await cache.adelete(f"user_{self.user.id}_channel")
                self.user.is_online = False
                await self.user.asave()
                if not self.user.is_invisible:
                    for user in self.user.friends.all():
                        chnls = cache.get(f"user_{user.id}_channel")

                        if chnls:
                            for chnl in chnls:
                                await self.channel_layer.send(
                                    chnl,
                                    {
                                        "type": "user.disconnected.sent",
                                        "from": self.user.username,
                                    },
                                )
                return

            await cache.aset(f"user_{self.user.id}_channel", channel)
        except (ValueError, AttributeError):
            pass

    async def receive(self, text_data):
        pass

    async def friend_request_sent(self, event):
        await self.send(json.dumps(event))

    async def friend_request_received(self, event):
        await self.send(json.dumps(event))

    async def friend_remove_sent(self, event):
        await self.send(json.dumps(event))

    async def friend_remove_received(self, event):
        await self.send(json.dumps(event))

    async def friend_accepted_sent(self, event):
        await self.send(json.dumps(event))

    async def friend_accepted_received(self, event):
        await self.send(json.dumps(event))

    async def friend_request_rejected_sent(self, event):
        await self.send(json.dumps(event))

    async def friend_request_rejected_received(self, event):
        await self.send(json.dumps(event))

    async def friend_request_removed_sent(self, event):
        await self.send(json.dumps(event))

    async def friend_request_removed_received(self, event):
        await self.send(json.dumps(event))

    async def block_user_sent(self, event):
        await self.send(json.dumps(event))

    async def block_user_received(self, event):
        await self.send(json.dumps(event))

    async def unblock_user_sent(self, event):
        await self.send(json.dumps(event))

    async def unblock_user_received(self, event):
        await self.send(json.dumps(event))

    async def dm_creation_sent(self, event):
        await self.send(json.dumps(event))

    async def dm_creation_received(self, event):
        await self.send(json.dumps(event))

    async def channel_creation_sent(self, event):
        await self.send(json.dumps(event))

    async def channel_creation_received(self, event):
        await self.send(json.dumps(event))

    async def channel_edit_sent(self, event):
        await self.send(json.dumps(event))

    async def channel_edit_received(self, event):
        await self.send(json.dumps(event))

    async def channel_delete_sent(self, event):
        await self.send(json.dumps(event))

    async def channel_delete_received(self, event):
        await self.send(json.dumps(event))

    async def channel_message_sent(self, event):
        await self.send(json.dumps(event))

    async def channel_message_received(self, event):
        await self.send(json.dumps(event))

    async def channel_message_edited(self, event):
        await self.send(json.dumps(event))

    async def channel_message_deleted(self, event):
        await self.send(json.dumps(event))

    async def channel_view_sent(self, event):
        await self.send(json.dumps(event))

    async def profile_update_sent(self, event):
        await self.send(json.dumps(event))

    async def profile_update_received(self, event):
        await self.send(json.dumps(event))

    async def user_connected_sent(self, event):
        await self.send(json.dumps(event))

    async def user_disconnected_sent(self, event):
        await self.send(json.dumps(event))
