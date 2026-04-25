from uuid import UUID

from django.db.models import Prefetch

from modules.chat.models import Conversation, ConversationMember


class ConversationMemberService:
    def __init__(self):
        pass

    def get_conversation_peer_user_ids_for_user(self, user_id: str | UUID) -> set:
        conversations = (
            Conversation.objects.filter(
                conversation_member__user_id=user_id,
                conversation_member__deleted_at=None,
                deleted_at=None,
            )
            .distinct()
            .prefetch_related(
                Prefetch(
                    "conversation_member",
                    queryset=(
                        ConversationMember.objects.filter(deleted_at=None).exclude(user_id=user_id)
                    ),
                )
            )
        )

        member_user_ids = set()
        for conversation in conversations:
            for member in conversation.conversation_member.all():
                member_user_ids.add(member.user_id)

        return member_user_ids
