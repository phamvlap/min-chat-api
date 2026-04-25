from uuid import UUID

from django.db.models import Q

from modules.friend.models import Friend
from modules.user.models import User


class FriendService:
    def __init__(self):
        pass

    def are_users_friends(self, user: User, destination_user: User) -> bool:
        return Friend.objects.filter(
            (Q(user=user, friend=destination_user) | Q(user=destination_user, friend=user)),
            deleted_at=None,
        ).exists()

    def get_friend_ids(self, user_id: str | UUID) -> set:
        friend_ids = set(
            Friend.objects.filter(
                user_id=user_id,
                deleted_at=None,
            ).values_list("friend_id", flat=True)
        )

        if isinstance(user_id, str):
            user_id = UUID(user_id)

        friend_ids.discard(user_id)

        return friend_ids
