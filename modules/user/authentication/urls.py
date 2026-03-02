from django.urls import path

from .views import GetStartedAPIView, RetrieveUpdateUserAPIView

urlpatterns = [
    path("get-started/", GetStartedAPIView.as_view(), name="get-started-api"),
    path("profile/", RetrieveUpdateUserAPIView.as_view(), name="user-retrieve-api"),
]
