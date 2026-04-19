from uuid import UUID

from base.constants import WebSocket
from modules.chat.models import Message, PinnedMessage
from modules.event_dispatch.services import EventDispatchService


class PinnedMessageService:
    def __init__(self):
        pass

    def get_pinned_message_in_conversation(
        self,
        message_id: str | UUID,
        conversation_id: str | UUID,
        *,
        select_related_fields: tuple = (),
    ) -> PinnedMessage | None:
        query = PinnedMessage.objects.filter(
            message_id=message_id,
            conversation_id=conversation_id,
            deleted_at=None,
        )
        if select_related_fields:
            query = query.select_related(*select_related_fields)
        return query.first()

    def unpin_message(self, pinned_message: PinnedMessage) -> None:
        message: Message = pinned_message.message
        # Delete the pinned message instance to unpin the message
        pinned_message.delete()

        # Send the unpinned message ID to the conversation group via Channels
        EventDispatchService().dispatch_event(
            entity=message,
            event_type=WebSocket.ServerEvent.Message.MESSAGE_UNPINNED,
            payload={
                "message_id": str(message.id),
            },
            group_name=WebSocket.Group.CONVERSATION.format(
                conversation_id=pinned_message.conversation.id
            ),
        )
