from rest_framework.permissions import IsAuthenticated

from base.views import BaseCreateAPIView, BaseRetrieveAPIView
from modules.user.models import User

from .serializers import GetStartedSerializer, UserSerializer


class GetStartedAPIView(BaseCreateAPIView):
    permission_classes = ()  # Allow anyone to access
    model = User
    serializer_class = GetStartedSerializer


class UserRetrieveAPIView(BaseRetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    model = User
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
