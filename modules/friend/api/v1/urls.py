from django.urls import include, path

from modules.friend.api.v1.views.user import ListFriendAPIView, RetrieveFriendAPIView

urlpatterns = [
    path(
        "user/friends/",
        include(
            [
                path("", ListFriendAPIView.as_view(), name="list-friend-api"),
                path(
                    "<uuid:friend_id>/",
                    RetrieveFriendAPIView.as_view(),
                    name="retrieve-friend-api",
                ),
            ]
        ),
    )
]
