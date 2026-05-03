from rest_framework import serializers

from base.exceptions import MediaDoesNotExistException
from modules.media.models import Media
from modules.media.serializers import (
    NestedMediaInCreateAndUpdateSerializer,
    NestedMediaInRetrieveSerializer,
)
from modules.user.models import User


class RetrieveUserSerializer(serializers.ModelSerializer):
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
            "clerk_user_id",
            "is_active",
            "avatar",
        )
        read_only_fields = fields


class UpdateUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(
        max_length=150,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    avatar = NestedMediaInCreateAndUpdateSerializer(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "avatar")

    def validate(self, attrs):
        if "avatar" in attrs:
            if attrs["avatar"] is not None:
                avatar_id = attrs["avatar"]["id"]
                media: Media | None = Media.objects.filter(
                    id=avatar_id,
                    deleted_at=None,
                    is_active=True,
                ).first()
                if not media:
                    raise MediaDoesNotExistException()
                attrs["avatar"] = media
            else:
                attrs["avatar"] = None
        return attrs

    def update(self, instance, validated_data):
        user: User = super().update(instance, validated_data)
        return RetrieveUserSerializer(user).data

    def to_representation(self, instance):
        return instance


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
