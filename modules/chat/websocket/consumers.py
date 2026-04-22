from typing import cast

import orjson
from asgiref.sync import async_to_sync

from base.constants import WebSocket
from base.consumers import BaseWebsocketConsumer
from modules.chat.permisisons import IsMemberOfConversation
from utils.exceptions import extract_serializer_error

from .dispatchers import CLIENT_EVENT_HANDLERS, SERVER_EVENT_HANDLERS


class ChatConsumer(BaseWebsocketConsumer):
    permission_classes = (IsMemberOfConversation,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Groups in which the channel will be added for broadcasting messages
        self.conversation_group_name = None
        self.user_group_name = None

        self.user = None
        self.conversation = None

    def connect(self):
        from modules.chat.services import ConversationService
        from modules.user.models import User

        # Check permissions
        if not self.check_permissions(self.scope):
            self.close()
            return

        # Assign current user
        if not self.scope["user"]:
            self.close()
            return

        self.user = cast(User, self.scope["user"])

        # Get conversation ID from URL route
        conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]

        # Retrieve the conversation
        conversation = ConversationService().get_conversation_by_id(conversation_id)

        # If conversation does not exist, close the connection
        if not conversation:
            self.close()
            return

        # Set conversation name and conversation object
        self.conversation_group_name = WebSocket.Group.CONVERSATION.format(
            conversation_id=conversation_id,
        )
        self.conversation = conversation

        # Add the channel to the conversation group for broadcasting messages
        async_to_sync(self.channel_layer.group_add)(self.conversation_group_name, self.channel_name)

        # Add the channel to the user group for sending user-specific events (e.g., message delivery receipts)
        self.user_group_name = WebSocket.Group.USER_IN_CONVERSATION.format(user_id=self.user.id)
        async_to_sync(self.channel_layer.group_add)(self.user_group_name, self.channel_name)

        # Accept the WebSocket connection
        self.accept()

    def disconnect(self, code):
        if self.conversation_group_name:
            async_to_sync(self.channel_layer.group_discard)(
                self.conversation_group_name,
                self.channel_name,
            )

        if self.user_group_name:
            async_to_sync(self.channel_layer.group_discard)(self.user_group_name, self.channel_name)

    def receive(self, text_data: str | None = None, bytes_data: bytes | None = None):
        data: dict = orjson.loads(text_data) if text_data else {}
        event_type: str = data["type"]

        # Dispatch the client event to the appropriate handler
        self._dispatch_client_event(event_type, data)

    def handle_send_message(self, data: dict):
        from modules.chat.services import MessageService

        from .serializers import SendMessageSerializer

        if not self.conversation or not self.conversation_group_name:
            self.send_error(code="conversation_not_found", message="Conversation not found.")
            return

        if not self.user or not self.user_group_name:
            self.send_error(
                code="authentication_required",
                message="Authentication credentials were not provided.",
            )
            return

        # Validate the incoming data
        serializer = SendMessageSerializer(data=data)
        if not serializer.is_valid():
            err_code, err_msg = extract_serializer_error(serializer.errors)
            self.send_error(code=err_code, message=err_msg)
            return

        MessageService().send_message(
            user=self.user,
            conversation=self.conversation,
            message_text=serializer.validated_data["message"],
            message_type=serializer.validated_data["message_type"],
        )

    def handle_message_delivered(self, data: dict):
        from modules.chat.services import MessageService

        from .serializers import DeliverMessageSerializer

        if not self.conversation or not self.conversation_group_name:
            self.send_error(code="conversation_not_found", message="Conversation not found.")
            return

        if not self.user or not self.user_group_name:
            self.send_error(
                code="authentication_required",
                message="Authentication credentials were not provided.",
            )
            return

        # Validate the incoming data
        serializer = DeliverMessageSerializer(data=data)
        if not serializer.is_valid():
            err_code, err_msg = extract_serializer_error(serializer.errors)
            self.send_error(code=err_code, message=err_msg)
            return

        validated_data = serializer.validated_data

        delivered_before = validated_data.get("delivered_before")

        MessageService().mark_message_as_delivered(
            user=self.user,
            conversation=self.conversation,
            delivered_before=delivered_before,
        )

    def handle_acknowledgment(self, data: dict):
        from modules.event_dispatch.services import EventDispatchService

        from .serializers import AcknowledgmentSerializer

        # Validate the incoming data
        serializer = AcknowledgmentSerializer(data=data)
        if not serializer.is_valid():
            return
        validated_data = serializer.validated_data

        EventDispatchService().mark_event_as_acknowledged(validated_data["event_dispatch_id"])

    def chat_message(self, event: dict):
        self._dispatch_server_event(event)

    def chat_message_delivered(self, event: dict):
        self._dispatch_server_event(event)

    def chat_message_pinned(self, event: dict):
        self._dispatch_server_event(event)

    def chat_message_unpinned(self, event: dict):
        self._dispatch_server_event(event)

    def chat_message_deleted_for_everyone(self, event: dict):
        self._dispatch_server_event(event)

    def chat_reaction_updated(self, event: dict):
        self._dispatch_server_event(event)

    def handle_new_message(self, event: dict):
        # Handle new message event from server
        self._send_message_to_client(event)

    def notify_sender_message_delivered(self, event: dict):
        # Send message delivered notification to the sender
        self._send_message_to_client(event)

    def notify_message_pinned(self, event: dict):
        # Send message pinned notification to clients
        self._send_message_to_client(event)

    def notify_message_unpinned(self, event: dict):
        # Send message unpinned notification to clients
        self._send_message_to_client(event)

    def notify_message_deleted_for_everyone(self, event: dict):
        # Send message deleted for everyone notification to clients
        self._send_message_to_client(event)

    def notify_reaction_updated(self, event: dict):
        # Send reaction updated notification to clients
        self._send_message_to_client(event)

    def _dispatch_client_event(self, event_type: str, data: dict) -> None:
        self.dispatch_event(
            CLIENT_EVENT_HANDLERS,
            event_type=event_type,
            data=data,
        )

    def _dispatch_server_event(self, event: dict) -> None:
        event_type: str | None = event.get("type")

        self.dispatch_event(
            SERVER_EVENT_HANDLERS,
            event_type=event_type if event_type else "",
            data=event,
        )

    def _send_message_to_client(self, message: dict) -> None:
        self.send(bytes_data=orjson.dumps(message))
