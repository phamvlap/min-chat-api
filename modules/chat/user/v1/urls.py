from django.urls import path

from .views import (
    CreateDirectConversationAPIView,
    DeleteMessageAPIView,
    ListConversationAPIView,
    ListMessageAPIView,
    ListMessageReactionAPIView,
    ListPinMessageAPIView,
    ReactMessageAPIView,
    ReadMessageAPIView,
    RetrieveConversationAPIView,
    UnpinMessageAPIView,
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
    path(
        "<uuid:conversation_id>/messages/pin/",
        ListPinMessageAPIView.as_view(),
        name="list-pin-message",
    ),
    path(
        "<uuid:conversation_id>/messages/unpin/",
        UnpinMessageAPIView.as_view(),
        name="unpin-message",
    ),
    path(
        "<uuid:conversation_id>/messages/delete/",
        DeleteMessageAPIView.as_view(),
        name="delete-message",
    ),
    path(
        "<uuid:conversation_id>/messages/react/",
        ReactMessageAPIView.as_view(),
        name="react-message",
    ),
    path(
        "<uuid:conversation_id>/messages/<uuid:message_id>/reactions/",
        ListMessageReactionAPIView.as_view(),
        name="list-message-reactions",
    ),
]
