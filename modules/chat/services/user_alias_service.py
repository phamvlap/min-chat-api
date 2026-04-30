from modules.chat.models import ConversationMember, UserAlias
from modules.user.models import User


class UserAliasService:
    def __init__(self):
        pass

    def update_or_create(
        self,
        *,
        user: User,
        target_member: ConversationMember,
        nickname: str,
    ) -> None:
        UserAlias.objects.update_or_create(
            user=user,
            target_member=target_member,
            deleted_at=None,
            defaults={"nickname": nickname},
        )

    def delete(self, *, user: User, target_member: ConversationMember) -> None:
        UserAlias.objects.filter(
            user=user,
            target_member=target_member,
            deleted_at=None,
        ).delete()
