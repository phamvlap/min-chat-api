import json

from channels.generic.websocket import WebsocketConsumer


class BaseWebsocketConsumer(WebsocketConsumer):
    permission_classes: tuple = ()

    def check_permissions(self, scope) -> bool:
        return all(permission.has_permission(scope) for permission in self.get_permissions())

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

    def dispatch_event(self, event_handlers: dict, event_type: str, data: dict):
        # If the event type is not recognized, ignore it safely
        if event_type not in event_handlers:
            return

        # Get the handler method name and method
        handler_method_name: str = event_handlers[event_type]
        handler_method = getattr(self, handler_method_name, None)

        # If the handler method does not exist, ignore safely
        if not handler_method:
            return

        # Call the handler method with the event
        handler_method(data)
