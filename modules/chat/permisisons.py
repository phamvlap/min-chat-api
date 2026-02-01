from base.permission import IsWebsocketUser


class IsMemberOfConversation(IsWebsocketUser):
    """
    Allows access only to users who are members of the conversation.
    """

    def has_permission(self, scope) -> bool:
        # Lazy import to ensure fully loaded models
        from modules.chat.models import ConversationMember

        user = scope.get("user")
        conversation_id = scope["url_route"]["kwargs"].get("conversation_id")

        if not super().has_permission(scope):
            return False

        if not conversation_id:
            return False

        return ConversationMember.objects.filter(
            conversation_id=conversation_id,
            conversation__deleted_at=None,
            user=user,
            deleted_at=None,
        ).exists()
