from uuid import UUID

import orjson
from django.db.models import Count

from base.constants import ChatConstants
from modules.chat.models import Conversation, ConversationMember, Message, MessageStatus
from modules.user.models import User


class ConversationService:
    def __init__(self):
        pass

    def get_direct_conversation(self, user: User, destination_user: User) -> Conversation | None:
        return (
            Conversation.objects.filter(
                type=Conversation.Types.DIRECT,
                conversation_member__user__in=[user, destination_user],
            )
            .annotate(member_count=Count("conversation_member"))
            .filter(member_count=2)
            .first()
        )

    def create_direct_conversation(self, user: User, destination_user: User) -> Conversation:
        conversation: Conversation = Conversation.objects.create(
            type=Conversation.Types.DIRECT,
            created_by=user.id,
        )

        # Add both users as members of the conversation
        members = ConversationMember.objects.bulk_create(
            [
                ConversationMember(
                    conversation=conversation,
                    user=user,
                    role=ConversationMember.MemberRoles.MEMBER,
                ),
                ConversationMember(
                    conversation=conversation,
                    user=destination_user,
                    role=ConversationMember.MemberRoles.MEMBER,
                ),
            ]
        )

        # Define the content of the first system message for the conversation
        first_message_content = {
            "event": ChatConstants.Conversation.Direct.SystemMessage.ConversationStarted.EVENT_NAME,
            "content": ChatConstants.Conversation.Direct.SystemMessage.ConversationStarted.MESSAGE.format(
                recipient_name=destination_user.full_name
            ),
        }

        message_data: dict = {
            "conversation": conversation,
            "sender": None,
            "message": orjson.dumps(first_message_content).decode("utf-8"),
            "message_type": Message.Types.SYSTEM,
        }

        # Create the first system message for the conversation
        message: Message = Message.objects.create(**message_data)

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

        return conversation

    def get_conversation_by_id(self, conversation_id: str | UUID) -> Conversation | None:
        return Conversation.objects.filter(id=conversation_id, deleted_at=None).first()
