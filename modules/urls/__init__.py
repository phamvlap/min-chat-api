from django.urls import include, path

from modules.chat.api.v1.urls import urlpatterns as chat_v1_urlpatterns
from modules.friend.api.v1.urls import urlpatterns as friend_v1_urlpatterns
from modules.friend_request.api.v1.urls import urlpatterns as friend_request_v1_urlpatterns
from modules.user.api.v1.urls import urlpatterns as user_v1_urlpatterns

urlpatterns = [
    path(
        "v1/",
        include(
            (
                (
                    *chat_v1_urlpatterns,
                    *friend_v1_urlpatterns,
                    *friend_request_v1_urlpatterns,
                    *user_v1_urlpatterns,
                ),
                "v1",
            ),
            namespace="v1",
        ),
    ),
]
