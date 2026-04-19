from base.permission import IsUser
from base.views import BaseListAPIView, BaseRetrieveAPIView
from modules.friend.api.v1.serializers.friend import ListFriendSerializer, RetrieveFriendSerializer
from modules.friend.models import Friend


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
            )
            .select_related("friend__avatar")
        )


class RetrieveFriendAPIView(BaseRetrieveAPIView):
    permission_classes = (IsUser,)
    model = Friend
    serializer_class = RetrieveFriendSerializer
    lookup_url_kwarg = "friend_id"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                user=self.request.user,
            )
            .select_related("friend__avatar")
        )
