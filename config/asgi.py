"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from base.authentication import ClerkAuthMiddleware
from modules.chat.websocket.routing import websocket_urlpatterns as chat_websocket_urlpatterns
from modules.user.websocket.routing import websocket_urlpatterns as user_websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

asgi_http_application = get_asgi_application()

websocket_urlpatterns = [
    *chat_websocket_urlpatterns,
    *user_websocket_urlpatterns,
]

application = ProtocolTypeRouter(
    {
        "http": asgi_http_application,
        "websocket": ClerkAuthMiddleware(
            URLRouter(websocket_urlpatterns),
        ),
    }
)
