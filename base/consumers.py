from typing import Any

import orjson
from channels.generic.websocket import WebsocketConsumer


class BaseWebsocketConsumer(WebsocketConsumer):
    permission_classes: tuple = ()
    client_event_handlers: dict[Any, str] = {}
    server_event_handlers: dict[Any, str] = {}

    def check_permissions(self, scope) -> bool:
        return all(permission.has_permission(scope) for permission in self.get_permissions())

    def get_permissions(self):
        return [permission() for permission in self.permission_classes]

    def send_error(self, code: str, message: str) -> None:
        self.send(
            bytes_data=orjson.dumps(
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

    def dispatch_client_event(self, event_type: str, data: dict) -> None:
        self.dispatch_event(
            self.client_event_handlers,
            event_type=event_type,
            data=data,
        )

    def dispatch_server_event(self, event: dict) -> None:
        event_type: str | None = event.get("type")

        self.dispatch_event(
            self.server_event_handlers,
            event_type=event_type if event_type else "",
            data=event,
        )

    def send_message(self, message: dict) -> None:
        self.send(text_data=orjson.dumps(message).decode("utf-8"))

    def handle_acknowledgment(self, data: dict):
        from base.serializers import AcknowledgmentSerializer
        from modules.event_dispatch.services import EventDispatchService

        # Validate the incoming data
        serializer = AcknowledgmentSerializer(data=data)
        if not serializer.is_valid():
            return
        validated_data = serializer.validated_data

        EventDispatchService().mark_event_as_acknowledged(validated_data["event_dispatch_id"])
