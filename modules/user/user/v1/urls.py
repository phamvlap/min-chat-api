from django.urls import path

from .views import DiscoverUserAPIView

urlpatterns = [
    path("discover/", DiscoverUserAPIView.as_view(), name="discover-user-api"),
]
