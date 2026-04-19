from django.utils import timezone

from base.constants import WebSocket
from modules.chat.models import Conversation, ConversationMember, Message, MessageVisibility
from modules.event_dispatch.services import EventDispatchService
from modules.user.models import User


class MessageVisibilityService:
    def __init__(self):
        pass

    def can_delete_for_everyone(self, user: User, message: Message) -> bool:
        return bool(message.sender and message.sender.id == user.id)

    def delete_message_for_user(
        self,
        user: User,
        message: Message,
        delete_for_everyone: bool = False,
    ) -> None:
        if delete_for_everyone:
            # If the message is already deleted for everyone, return 204 No Content without doing anything
            if message.is_deleted_for_everyone:
                return

            # Mark the message as deleted for everyone
            message.is_deleted_for_everyone = True
            message.deleted_for_everyone_at = timezone.now()
            message.deleted_for_everyone_by = user
            message.save(
                update_fields=[
                    "is_deleted_for_everyone",
                    "deleted_for_everyone_at",
                    "deleted_for_everyone_by",
                ]
            )

            # Notify all members in the conversation about the message being deleted for everyone
            EventDispatchService().dispatch_event(
                entity=message,
                event_type=WebSocket.ServerEvent.Message.MESSAGE_DELETED_FOR_EVERYONE,
                payload={
                    "message_id": str(message.id),
                },
                group_name=WebSocket.Group.CONVERSATION.format(
                    conversation_id=message.conversation.id
                ),
            )
        else:
            # Mark the message as hidden for the user
            MessageVisibility.objects.update_or_create(
                message=message,
                user=user,
                defaults={
                    "is_hidden": True,
                    "hidden_at": timezone.now(),
                },
            )

            # Update the last visible message for the user in the conversation if necessary
            self._update_last_message_for_user(user, message)

        return

    def _update_last_message_for_user(self, user: User, message: Message):
        # Get the ConversationMember instance for the user and conversation
        member = (
            ConversationMember.objects.filter(
                conversation=message.conversation,
                user=user,
                deleted_at=None,
            )
            .select_related("last_visible_message")
            .first()
        )

        # Only update the last visible message if the deleted message is currently the last visible message for the user
        if member and member.last_visible_message == message:
            # Find the new last visible message for the user in the conversation
            new_last_message = self._find_new_last_message(message.conversation, user)

            # Update the last visible message for the user in the conversation
            member.last_visible_message = new_last_message
            member.save(update_fields=["last_visible_message"])

    def _find_new_last_message(self, conversation: Conversation, user: User) -> Message | None:
        return (
            Message.objects.filter(
                conversation=conversation,
                conversation__deleted_at=None,
            )
            .exclude(message_visibility__user=user, message_visibility__is_hidden=True)
            .order_by("-created_at")
            .first()
        )
