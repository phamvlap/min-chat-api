from django.urls import path

from .views import CreateDirectConversationAPIView, ListConversationAPIView

urlpatterns = [
    path("direct/", CreateDirectConversationAPIView.as_view(), name="create_direct_conversation"),
    path("", ListConversationAPIView.as_view(), name="list_conversations"),
]
