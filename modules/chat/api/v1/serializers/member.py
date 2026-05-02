from rest_framework import serializers

from base.constants import ResponseStatus
from modules.chat.api.v1.serializers.message import NestedMessageSerializer
from modules.chat.models import ConversationMember
from modules.chat.services import UserAliasService
from modules.user.api.v1.serializers.user import NestedRestrictedUserSerializer
from modules.user.models import User


class NestedConversationMemberSerializer(serializers.ModelSerializer):
    user = NestedRestrictedUserSerializer(read_only=True)
    last_visible_message = NestedMessageSerializer(read_only=True)
    nickname = serializers.CharField(read_only=True)

    class Meta:
        model = ConversationMember
        fields = (
            "id",
            "user",
            "role",
            "muted_until",
            "last_read_at",
            "last_visible_message",
            "nickname",
        )
        read_only_fields = fields


class SetNicknameForMemberInConversationSerializer(serializers.ModelSerializer):
    nickname = serializers.CharField(
        required=False,
        max_length=256,
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = ConversationMember
        fields = ("nickname",)

    def update(self, instance, validated_data):
        if "nickname" in validated_data:
            view = self.context.get("view")
            user: User | None = view.request.user if view and view.request else None

            if not user:
                raise serializers.ValidationError("Authentication credentials were not provided.")

            nickname = validated_data["nickname"]

            if nickname is None or nickname == "":
                # If nickname is None or empty string, delete the UserAlias if it exists
                UserAliasService().delete(user=user, target_member=instance)
            else:
                # Otherwise, create or update the UserAlias with the new nickname
                UserAliasService().update_or_create(
                    user=user,
                    target_member=instance,
                    nickname=nickname,
                )

        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Nickname updated successfully.",
        }

    def to_representation(self, instance):
        return instance
