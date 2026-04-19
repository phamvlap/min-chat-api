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
