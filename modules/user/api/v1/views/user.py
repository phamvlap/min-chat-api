from django.db.models import Exists, OuterRef, Q

from base.permission import IsAuthenticated
from base.views import BaseListAPIView
from modules.friend.models import Friend
from modules.friend_request.models import FriendRequest
from modules.user.api.v1.serializers.user import DiscoverUserSerializer
from modules.user.models import User


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
                | Exists(
                    Friend.objects.filter(
                        Q(
                            user_id=self.request.user.id,
                            friend_id=OuterRef("id"),
                            friend__deleted_at=None,
                        )
                        | Q(
                            user_id=OuterRef("id"),
                            friend_id=self.request.user.id,
                            user__deleted_at=None,
                        ),
                        deleted_at=None,
                    )
                )
                | Exists(
                    FriendRequest.objects.filter(
                        Q(
                            sender_id=self.request.user.id,
                            receiver_id=OuterRef("id"),
                            receiver__deleted_at=None,
                        )
                        | Q(
                            sender_id=OuterRef("id"),
                            receiver_id=self.request.user.id,
                            sender__deleted_at=None,
                        ),
                        status__in=FriendRequest.exclude_statuses_on_creation(),
                        deleted_at=None,
                    )
                )
            )
            .select_related("avatar")
        )
