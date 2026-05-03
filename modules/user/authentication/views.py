from base.constants import ViewAction
from base.exceptions import UserNotFoundException
from base.permission import IsAuthenticated
from base.views import BaseCreateAPIView, BaseRetrieveAPIView, BaseUpdateAPIView
from modules.user.models import User

from .serializers import GetStartedSerializer, RetrieveUserSerializer, UpdateUserSerializer


class GetStartedAPIView(BaseCreateAPIView):
    permission_classes = ()  # Allow anyone to access
    model = User
    serializer_class = GetStartedSerializer


class RetrieveUpdateUserAPIView(BaseRetrieveAPIView, BaseUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    model = User

    def get_serializer_class(self):
        if self.action == ViewAction.UPDATE:
            return UpdateUserSerializer
        return RetrieveUserSerializer

    def get_object(self):
        user: User | None = (
            self.model.objects.filter(id=self.request.user.id, deleted_at=None)
            .select_related("avatar")
            .first()
        )

        if not user:
            raise UserNotFoundException()
        return user
