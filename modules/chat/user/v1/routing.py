from typing import Any, cast

from django.urls import re_path

from .consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(
        r"ws/conversations/(?P<conversation_id>[0-9a-f-]+)/$", cast(Any, ChatConsumer.as_asgi())
    ),
]
