from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class WebSocketService:
    def __init__(self):
        self.channel_layer = get_channel_layer()

    def send_message(self, group_name: str, payload: dict):
        async_to_sync(self.channel_layer.group_send)(group_name, payload)
