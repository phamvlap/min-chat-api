from rest_framework.generics import CreateAPIView

from modules.user.models import User

from .serializers import CreateSessionTokenSerializer


class CreateSessionTokenAPIView(CreateAPIView):
    permission_classes = ()  # Allow anyone to access
    serializer_class = CreateSessionTokenSerializer
    model = User
