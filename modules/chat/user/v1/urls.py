from django.urls import path

from .views import (
    CreateDirectConversationAPIView,
    ListConversationAPIView,
    ListMessageAPIView,
    ReadMessageAPIView,
    RetrieveConversationAPIView,
)

urlpatterns = [
    path("direct/", CreateDirectConversationAPIView.as_view(), name="create-direct-conversation"),
    path("", ListConversationAPIView.as_view(), name="list-conversations"),
    path(
        "<uuid:conversation_id>/",
        RetrieveConversationAPIView.as_view(),
        name="retrieve-conversation",
    ),
    path(
        "<uuid:conversation_id>/messages/",
        ListMessageAPIView.as_view(),
        name="list-messages",
    ),
    path(
        "<uuid:conversation_id>/messages/read/",
        ReadMessageAPIView.as_view(),
        name="read-messages",
    ),
]
