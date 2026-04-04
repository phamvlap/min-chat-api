from django.urls import path

from .views import ListFriendAPIView, RetrieveFriendAPIView

urlpatterns = [
    path("", ListFriendAPIView.as_view(), name="list-friend-api"),
    path("<uuid:friend_id>/", RetrieveFriendAPIView.as_view(), name="retrieve-friend-api"),
]
