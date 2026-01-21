from django.urls import include, path

from .admin_urls import urlpatterns as admin_urlpatterns
from .user_urls import urlpatterns as user_urlpatterns

urlpatterns = [
    path("user/admin/", include((admin_urlpatterns, "admin"), namespace="admin")),
    path("user/", include((user_urlpatterns, "user"), namespace="user")),
]
