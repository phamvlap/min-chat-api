from rest_framework import serializers

from modules.user.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_user",
            "clerk_user_id",
            "is_active",
        )
        read_only_fields = fields


class GetStartedSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=256)

    class Meta:
        model = User
        fields = ("username",)

    def create(self, validated_data):
        user: User | None = self.Meta.model.objects.filter(
            username=validated_data["username"],
            deleted_at=None,
        ).first()

        return {
            "id": user.id if user else None,
            "username": validated_data["username"],
            "email": user.email if user else None,
            "is_user": user.is_user if user else False,
            "is_active": user.is_active if user else False,
            "clerk_user_id": user.clerk_user_id if user else None,
        }

    def to_representation(self, instance):
        return instance
