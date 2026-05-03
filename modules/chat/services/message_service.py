from uuid import UUID

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from base.constants import WebSocket
from modules.chat.models import (
    Conversation,
    ConversationMember,
    Message,
    MessageRevision,
    MessageStatus,
)
from modules.event_dispatch.services import EventDispatchService
from modules.user.models import User


class MessageService:
    def __init__(self):
        pass

    def get_message_in_conversation(
        self,
        message_id: str | UUID,
        conversation_id: str | UUID,
        *,
        select_related_fields: tuple = (),
    ) -> Message | None:
        queryset = Message.objects.filter(
            id=message_id,
            conversation_id=conversation_id,
            deleted_at=None,
        )
        if select_related_fields:
            queryset = queryset.select_related(*select_related_fields)
        return queryset.first()

    def send_message(
        self,
        user: User,
        conversation: Conversation,
        message_text: str,
        message_type: str,
    ) -> None:
        from modules.chat.api.v1.serializers.message import SendMessageEventPayloadSerializer

        # Prepare message data
        message_data: dict = {
            "conversation": conversation,
            "sender": user,
            "message": message_text,
            "message_type": message_type,
        }

        # Create a new message
        message: Message = Message.objects.create(**message_data)

        # Get all conversation members
        members: QuerySet[ConversationMember] = ConversationMember.objects.filter(
            conversation=conversation,
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
        conversation.last_message = message
        conversation.last_message_at = message.created_at
        conversation.save(update_fields=["last_message", "last_message_at"])

        # Update last visible message for each member
        ConversationMember.objects.filter(
            conversation=conversation,
            deleted_at=None,
        ).update(last_visible_message=message)

        # Build the message data to be sent to clients
        message_payload = SendMessageEventPayloadSerializer(message).data

        EventDispatchService().dispatch_event(
            entity=message,
            event_type=WebSocket.ServerEvent.Message.MESSAGE,
            payload=message_payload,
            group_name=WebSocket.Group.CONVERSATION.format(conversation_id=str(conversation.id)),
        )

    def mark_message_as_delivered(
        self,
        user: User,
        conversation: Conversation,
        delivered_before: str,
    ) -> None:
        # Get all message statuses for the current user in the conversation that are still marked as SENT
        # and were created before the specified timestamp
        messages_to_update_delivery = MessageStatus.objects.filter(
            user=user,
            message__conversation=conversation,
            message__conversation__deleted_at=None,
            message__deleted_at=None,
            message__created_at__lte=delivered_before,
            status=MessageStatus.StatusChoices.SENT,
            deleted_at=None,
        ).select_related("message__sender")

        # Get all messages in the conversation and annotate them with the delivery status for the current user
        messages = [msg_status.message for msg_status in messages_to_update_delivery]

        # Get unique sender IDs from the messages to send delivery notifications to the respective senders
        sender_ids = {msg.sender.id for msg in messages if msg.sender}

        # Update message statuses to delivered for messages created before the specified timestamp
        messages_to_update_delivery.update(status=MessageStatus.StatusChoices.DELIVERED)

        # Send message delivered notifications to the respective senders for the messages that were marked as delivered
        event_dispatcher = EventDispatchService()
        payload = {
            "conversation_id": conversation.id,
            "delivered_before": delivered_before,
        }
        for sender_id in sender_ids:
            event_dispatcher.dispatch_event(
                entity=conversation,
                event_type=WebSocket.ServerEvent.Message.MESSAGE_DELIVERED,
                payload=payload,
                group_name=WebSocket.Group.USER_IN_CONVERSATION.format(user_id=sender_id),
            )

    def read_message(self, user: User, conversation_id: str | UUID, read_before: str) -> int:
        # Update message statuses of messages that are before the read_before timestamp to READ
        read_count: int = (
            MessageStatus.objects.filter(
                user=user,
                message__conversation__id=conversation_id,
                message__created_at__lte=read_before,
                deleted_at=None,
            )
            .exclude(status=MessageStatus.StatusChoices.READ, message__sender=user)
            .update(status=MessageStatus.StatusChoices.READ)
        )

        # Also update the last_read_at timestamp in ConversationMember
        ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user=user,
            deleted_at=None,
        ).update(last_read_at=read_before)

        return read_count

    def edit_message(
        self,
        *,
        message: Message,
        user: User,
        new_message_content: str,
        new_message_type: Message.Types,
    ) -> Message:
        with transaction.atomic():
            message = Message.objects.select_for_update().get(id=message.id, deleted_at=None)

            # Create a message revision before updating the message
            MessageRevision.objects.create(
                message=message,
                message_content=new_message_content,
                message_type=new_message_type,
                old_message_content=message.message,
                old_message_type=message.message_type,
                version=message.version + 1,
                created_by=user.id,
            )

            # Update the message content and message type
            message.message = new_message_content
            message.message_type = new_message_type
            message.version += 1
            message.modified_by = user.id
            message.is_edited = True
            message.edited_at = timezone.now()
            message.edited_by = user

            message.save(
                update_fields=[
                    "message",
                    "message_type",
                    "version",
                    "modified_by",
                    "modified_at",
                    "is_edited",
                    "edited_at",
                    "edited_by",
                ]
            )

            # Send message update notification to conversation members
            payload: dict = {
                "message_id": message.id,
                "new_message": message.message,
                "new_message_type": message.message_type,
                "edited_at": message.edited_at,
            }

            EventDispatchService().dispatch_event(
                entity=message,
                event_type=WebSocket.ServerEvent.Message.MESSAGE_UPDATE,
                payload=payload,
                group_name=WebSocket.Group.CONVERSATION.format(
                    conversation_id=str(message.conversation.id)
                ),
            )

        return message
