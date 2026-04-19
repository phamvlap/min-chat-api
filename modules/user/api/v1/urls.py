from django.urls import include, path

from modules.user.api.v1.views.user import DiscoverUserAPIView

urlpatterns = [
    path(
        "user/users/",
        include(
            [
                path("discover/", DiscoverUserAPIView.as_view(), name="discover-user-api"),
            ]
        ),
    )
]
