from base.constants import ChatConstants, WebSocket
from modules.chat.models import Message, MessageReaction
from modules.event_dispatch.services import EventDispatchService
from modules.user.models import User


class MessageReactionService:
    def __init__(self):
        pass

    def toggle_reaction(self, user: User, message: Message, reaction_type: str) -> str:
        # Check if the same reaction already exists for the message by the user
        existing_reaction = MessageReaction.objects.filter(
            message=message,
            user=user,
            reaction_type=reaction_type,
            deleted_at=None,
        ).first()

        if existing_reaction:
            # If the same reaction already exists, remove it (toggle off)
            existing_reaction.delete()
            reaction_status = ChatConstants.Message.ReactionStatus.REMOVED
        else:
            # Otherwise, create a new reaction (toggle on)
            MessageReaction.objects.create(
                message=message,
                user=user,
                reaction_type=reaction_type,
            )
            reaction_status = ChatConstants.Message.ReactionStatus.ADDED

        # Send the updated reaction status to the conversation group via Channels
        EventDispatchService().dispatch_event(
            entity=message,
            event_type=WebSocket.ServerEvent.Message.REACTION_UPDATED,
            payload={
                "message_id": str(message.id),
                "reaction_type": reaction_type,
                "reaction_status": reaction_status,
            },
            group_name=WebSocket.Group.CONVERSATION.format(conversation_id=message.conversation.id),
        )

        return reaction_status
