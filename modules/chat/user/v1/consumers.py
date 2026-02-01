from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]

        self.conversation_name = f"conversation.{conversation_id}"

        async_to_sync(self.channel_layer.group_add)(self.conversation_name, self.channel_name)

        self.accept()
