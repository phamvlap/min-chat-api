from rest_framework import serializers

from modules.media.serializers import NestedMediaInRetrieveSerializer
from modules.user.models import User


class NestedUserSerializer(serializers.ModelSerializer):
    avatar = NestedMediaInRetrieveSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_user",
            "avatar",
        )
        read_only_fields = fields
