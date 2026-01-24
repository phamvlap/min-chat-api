from django.db.models import Q

from base.constants import ViewAction
from base.permission import IsUser
from base.views import BaseCreateAPIView, BaseListAPIView, BaseUpdateAPIView
from modules.friend_request.models import FriendRequest

from .serializers import (
    CancelFriendRequestSerializer,
    CreateFriendRequestSerializer,
    ListFriendRequestSerializer,
    AcceptOrRejectFriendRequestSerializer,
)


class ListCreateFriendRequestAPIView(BaseListAPIView, BaseCreateAPIView):
    permission_classes = (IsUser,)
    model = FriendRequest
    serializer_class = CreateFriendRequestSerializer

    def get_serializer_class(self):
        if self.action == ViewAction.CREATE:
            return CreateFriendRequestSerializer
        return ListFriendRequestSerializer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(sender=self.request.user) | Q(receiver=self.request.user),
                status=FriendRequest.Status.PENDING,
            )
        )


class CancelFriendRequestAPIView(BaseUpdateAPIView):
    permission_classes = (IsUser,)
    model = FriendRequest
    serializer_class = CancelFriendRequestSerializer
    lookup_url_kwarg = "friend_request_id"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                sender=self.request.user,
                status=FriendRequest.Status.PENDING,
            )
        )


class AcceptOrRejectFriendRequestAPIView(BaseUpdateAPIView):
    permission_classes = (IsUser,)
    model = FriendRequest
    serializer_class = AcceptOrRejectFriendRequestSerializer
    lookup_url_kwarg = "friend_request_id"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                receiver=self.request.user,
                status=FriendRequest.Status.PENDING,
            )
        )
