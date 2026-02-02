import json

from channels.generic.websocket import WebsocketConsumer


class BaseWebsocketConsumer(WebsocketConsumer):
    permission_classes: tuple = ()

    def check_permissions(self, scope) -> bool:
        for permission in self.get_permissions():
            if not permission.has_permission(scope):
                return False
        return True

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def send_error(self, code: str, message: str) -> None:
        self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "code": code,
                    "message": message,
                }
            )
        )
