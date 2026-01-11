from django.urls import path

from .views import GetStartedAPIView, UserRetrieveAPIView

urlpatterns = [
    path("get-started/", GetStartedAPIView.as_view(), name="get-started-api"),
    path("profile/", UserRetrieveAPIView.as_view(), name="user-retrieve-api"),
]
