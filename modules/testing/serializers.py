from rest_framework import serializers

from modules.user.models import User
from services.clerk_service import ClerkService


class CreateSessionTokenSerializer(serializers.ModelSerializer):
    username = serializers.CharField()

    class Meta:
        model = User
        fields = ("username",)

    def create(self, validated_data):
        # Find user by username
        user: User | None = self.Meta.model.objects.filter(
            username=validated_data["username"],
            deleted_at=None,
        ).first()
        if not user:
            raise serializers.ValidationError("User with this username does not exist.")

        user_id = str(user.clerk_user_id)

        # Create sign-in token via ClerkService
        clerk_service = ClerkService()

        session: dict | None = clerk_service.create_new_session(user_id=user_id)
        if not session or "id" not in session:
            raise serializers.ValidationError("Failed to create session.")

        token_data: dict | None = clerk_service.create_session_token(session_id=session["id"])
        if not token_data:
            raise serializers.ValidationError("Failed to create session token.")

        if "errors" in token_data:
            raise serializers.ValidationError(token_data["errors"])

        return token_data

    def to_representation(self, instance):
        return instance
