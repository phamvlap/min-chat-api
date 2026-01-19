from django.urls import path

from .views import CreateSessionTokenAPIView

urlpatterns = [
    path(
        "create-session-token/",
        CreateSessionTokenAPIView.as_view(),
        name="create-session-token-api",
    ),
]
