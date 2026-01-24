from rest_framework import serializers

from modules.user.models import User


class NestedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_user",
        )
        read_only_fields = fields
