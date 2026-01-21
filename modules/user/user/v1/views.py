from django.db.models import Q

from base.permission import IsAuthenticated
from base.views import BaseListAPIView
from modules.friend_request.models import FriendRequest
from modules.user.models import User

from .serializers import DiscoverUserSerializer


class DiscoverUserAPIView(BaseListAPIView):
    permission_classes = (IsAuthenticated,)
    model = User
    serializer_class = DiscoverUserSerializer
    search_fields = ("username", "first_name", "last_name", "email")
    ordering_fields = ("username", "first_name", "last_name", "email")

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_user=True, is_active=True)
            .exclude(
                Q(id=self.request.user.id)
                | Q(user_friend__user=self.request.user, user_friend__deleted_at=None)
                | Q(user_friend__friend=self.request.user, user_friend__deleted_at=None)
                | Q(
                    sender_friend_request__sender=self.request.user,
                    sender_friend_request__status__in=FriendRequest.excluded_discovery_statuses(),
                    sender_friend_request__deleted_at=None,
                )
                | Q(
                    receiver_friend_request__receiver=self.request.user,
                    receiver_friend_request__status__in=FriendRequest.excluded_discovery_statuses(),
                    receiver_friend_request__deleted_at=None,
                )
            )
        )
