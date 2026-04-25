from rest_framework import serializers

from modules.chat.models import Message
from modules.user.serializers import NestedRestrictedUserSerializer

from .message_reaction import MessageReactionInMessageListSerializer


class NestedMessageSerializer(serializers.ModelSerializer):
    sender = NestedRestrictedUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "message",
            "message_type",
            "created_at",
            "is_deleted_for_everyone",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # If the message is deleted for everyone, hidden the message content and related fields in the representation
        if instance.is_deleted_for_everyone:
            representation["message"] = None
            representation["replied_to"] = None

        return representation


class ListMessageSerializer(serializers.ModelSerializer):
    sender = NestedRestrictedUserSerializer(read_only=True)
    replied_to = "self"  # Recursive relationship for nested replies
    status = serializers.CharField(read_only=True)
    is_pinned = serializers.BooleanField(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "message",
            "message_type",
            "created_at",
            "replied_to",
            "status",
            "is_pinned",
            "is_deleted_for_everyone",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # If the message is deleted for everyone, hidden the message content and related fields in the representation
        if instance.is_deleted_for_everyone:
            representation["message"] = None
            representation["replied_to"] = None

        message_reaction_mapping = self.context.get("message_reaction_mapping", {})
        message_id_str = str(instance.id)

        representation["reactions"] = MessageReactionInMessageListSerializer(
            message_reaction_mapping.get(message_id_str, []),
            many=True,
            read_only=True,
        ).data

        return representation


class ReadMessageSerializer(serializers.Serializer):
    read_before = serializers.DateTimeField()
