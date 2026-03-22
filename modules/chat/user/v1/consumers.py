import json
from typing import Any

from asgiref.sync import async_to_sync
from django.db.models import QuerySet

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
        from modules.chat.models import Conversation

        # Check permissions
        if not self.check_permissions(self.scope):
            self.close()
            return

        # Assign current user
        self.user = self.scope["user"]

        # Get conversation ID from URL route
        conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]

        # Retrieve the conversation
        conversation: Conversation | None = Conversation.objects.filter(
            id=conversation_id,
            deleted_at=None,
        ).first()

        # If conversation does not exist, close the connection
        if not conversation:
            self.close()
            return

        # Set conversation name and conversation object
        self.conversation_group_name = f"conversation.{conversation_id}"
        self.conversation = conversation

        # Add the channel to the conversation group for broadcasting messages
        async_to_sync(self.channel_layer.group_add)(self.conversation_group_name, self.channel_name)

        # Add the channel to the user group for sending user-specific events (e.g., message delivery receipts)
        self.user_group_name = f"user.{self.user.id}"
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
        data: dict = json.loads(text_data) if text_data else {}
        event_type: str = data["type"]

        # Dispatch the client event to the appropriate handler
        self._dispatch_client_event(event_type, data)

    def handle_send_message(self, data: dict):
        from modules.chat.models import ConversationMember, Message, MessageStatus

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

        # Prepare message data
        validated_data = serializer.validated_data

        message_data: dict = {
            "conversation": self.conversation,
            "sender": self.user,
            "message": validated_data.get("message", ""),
            "message_type": validated_data.get("message_type", ""),
        }

        # Create a new message
        message: Message = Message.objects.create(**message_data)

        # Get all conversation members
        members: QuerySet[ConversationMember] = ConversationMember.objects.filter(
            conversation=self.conversation,
            deleted_at=None,
        )

        # Create message status for each member
        message_statuses: list[MessageStatus] = []
        for member in members:
            message_status: MessageStatus = MessageStatus(
                message=message,
                user=member.user,
                status=MessageStatus.StatusChoices.SENT,
            )
            message_statuses.append(message_status)

        # Bulk create message statuses
        MessageStatus.objects.bulk_create(message_statuses)

        # Update the last message in the conversation
        self.conversation.last_message = message
        self.conversation.last_message_at = message.created_at
        self.conversation.save(update_fields=["last_message", "last_message_at"])

        # Update last visible message for each member
        ConversationMember.objects.filter(
            conversation=self.conversation,
            deleted_at=None,
        ).update(last_visible_message=message)

        # Build the message data to be sent to clients
        sender_avatar: dict[str, Any] | None = None

        if self.user.avatar:
            sender_avatar = {
                "id": str(self.user.avatar.id),
                "key": self.user.avatar.key,
                "key_type": self.user.avatar.key_type,
                "original_name": self.user.avatar.original_name,
                "file_size": self.user.avatar.file_size,
                "public": self.user.avatar.public,
                "public_url": self.user.avatar.public_url,
            }

        client_message_payload: dict[str, Any] = {
            "type": WebSocket.ServerEvent.Message.MESSAGE,
            "conversation_id": str(self.conversation.id),
            "sender": {
                "id": str(self.user.id),
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "email": self.user.email,
                "is_user": bool(self.user.is_user),
                "avatar": sender_avatar,
            },
            "message_id": str(message.id),
            "message": message.message,
            "message_type": message.message_type,
            "created_at": message.created_at.isoformat(),
        }

        # Broadcast the new message to all group members
        async_to_sync(self.channel_layer.group_send)(
            self.conversation_group_name,
            client_message_payload,
        )

    def handle_message_delivered(self, data: dict):
        from modules.chat.models import MessageStatus

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

        # Get all message statuses for the current user in the conversation that are still marked as SENT
        # and were created before the specified timestamp
        messages_to_update_delivery = MessageStatus.objects.filter(
            user=self.user,
            message__conversation=self.conversation,
            message__conversation__deleted_at=None,
            message__deleted_at=None,
            message__created_at__lte=delivered_before,
            status=MessageStatus.StatusChoices.SENT,
            deleted_at=None,
        ).select_related("message__sender")

        # Update message statuses to delivered for messages created before the specified timestamp
        messages_to_update_delivery.update(status=MessageStatus.StatusChoices.DELIVERED)

        # Get all messages in the conversation and annotate them with the delivery status for the current user
        messages = [msg_status.message for msg_status in messages_to_update_delivery]

        # Get unique sender IDs from the messages to send delivery notifications to the respective senders
        sender_ids = {msg.sender.id for msg in messages}

        # Send message delivered notifications to the respective senders for the messages that were marked as delivered
        for sender_id in sender_ids:
            async_to_sync(self.channel_layer.group_send)(
                f"user.{sender_id}",
                {
                    "type": WebSocket.ServerEvent.Message.MESSAGE_DELIVERED,
                    "conversation_id": str(self.conversation.id),
                    "delivered_before": delivered_before.isoformat(),
                },
            )

    def chat_message(self, event: dict):
        self._dispatch_server_event(event)

    def chat_message_delivered(self, event: dict):
        self._dispatch_server_event(event)

    def handle_new_message(self, event: dict):
        # Handle new message event from server
        self.send(text_data=json.dumps(event))

    def notify_sender_message_delivered(self, event: dict):
        # Send message delivered notification to the sender
        self.send(text_data=json.dumps(event))

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
