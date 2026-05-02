from rest_framework import serializers

from modules.media.serializers import NestedMediaInRetrieveSerializer
from modules.user.models import User
from modules.user.services import PresenceService


class DiscoverUserSerializer(serializers.ModelSerializer):
    avatar = NestedMediaInRetrieveSerializer(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "email", "avatar")
        read_only_fields = fields


class NestedPublicUserSerializer(serializers.ModelSerializer):
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


class NestedRestrictedUserSerializer(serializers.ModelSerializer):
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
            "last_seen_at",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Add online status to the representation using the PresenceService
        presence_service = PresenceService()
        representation["is_online"] = presence_service.is_user_online(str(instance.id))

        return representation
