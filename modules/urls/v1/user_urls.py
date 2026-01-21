from django.urls import include, path

from modules.user.user.v1.urls import urlpatterns as user_urlpatterns

urlpatterns = [
    path("users/", include((user_urlpatterns, "user"), namespace="user")),
]
