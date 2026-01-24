from base.permission import IsUser
from base.views import BaseListAPIView
from modules.friend.models import Friend

from .serializers import ListFriendSerializer


class ListFriendAPIView(BaseListAPIView):
    permission_classes = (IsUser,)
    model = Friend
    serializer_class = ListFriendSerializer
    search_fields = ("friend__username", "friend__first_name", "friend__last_name", "friend__email")
    ordering_fields = (
        "friend__username",
        "friend__first_name",
        "friend__last_name",
        "friend__email",
        "created_at",
    )

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                user=self.request.user,
                deleted_at=None,
            )
            .select_related("friend")
        )
