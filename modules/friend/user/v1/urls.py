from django.urls import path

from .views import ListFriendAPIView

urlpatterns = [
    path("", ListFriendAPIView.as_view(), name="list-friend-api"),
]
