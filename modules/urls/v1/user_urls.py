from django.urls import include, path

from modules.chat.user.v1.urls import urlpatterns as chat_urlpatterns
from modules.friend.user.v1.urls import urlpatterns as friend_urlpatterns
from modules.friend_request.user.v1.urls import urlpatterns as friend_request_urlpatterns
from modules.user.user.v1.urls import urlpatterns as user_urlpatterns

urlpatterns = [
    path("users/", include((user_urlpatterns, "user"), namespace="user")),
    path(
        "friend-requests/",
        include((friend_request_urlpatterns, "friend_request"), namespace="friend_request"),
    ),
    path("friends/", include((friend_urlpatterns, "friend"), namespace="friend")),
    path("conversations/", include((chat_urlpatterns, "chat"), namespace="chat")),
]
