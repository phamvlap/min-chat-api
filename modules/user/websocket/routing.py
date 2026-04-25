from typing import Any, cast

from django.urls import re_path

from .consumers import UserPresenceConsumer

websocket_urlpatterns = [
    re_path(r"ws/users/presence/$", cast(Any, UserPresenceConsumer.as_asgi())),
]
