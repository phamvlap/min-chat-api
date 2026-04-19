from django.urls import include, path, register_converter

from base.converters import FriendRequestActionConverter
from modules.friend_request.api.v1.views.user import (
    AcceptOrRejectFriendRequestAPIView,
    CancelFriendRequestAPIView,
    ListCreateFriendRequestAPIView,
)

register_converter(FriendRequestActionConverter, "friend_request_action")

urlpatterns = [
    path(
        "user/friend-requests/",
        include(
            [
                path(
                    "",
                    ListCreateFriendRequestAPIView.as_view(),
                    name="list-create-friend-request-api",
                ),
                path(
                    "<uuid:friend_request_id>/cancel/",
                    CancelFriendRequestAPIView.as_view(),
                    name="cancel-friend-request-api",
                ),
                path(
                    "<uuid:friend_request_id>/<friend_request_action:action>/",
                    AcceptOrRejectFriendRequestAPIView.as_view(),
                    name="accept-reject-friend-request-api",
                ),
            ]
        ),
    )
]
