from datetime import timedelta
from typing import cast

from django.utils import timezone
from rest_framework import serializers

from base.constants import ChatConstants, ResponseStatus
from modules.chat.models import Message, MessageStatus
from modules.chat.services.message_service import MessageService
from modules.user.api.v1.serializers.user import NestedRestrictedUserSerializer
from modules.user.models import User

from .message_reaction import MessageReactionInMessageListSerializer


class NestedRepliedMessageSerializer(serializers.ModelSerializer):
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
            "is_edited",
        )
        read_only_fields = fields


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
            "is_edited",
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
    replied_to = NestedRepliedMessageSerializer(read_only=True)
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
            "replied_message_snapshot",
            "status",
            "is_pinned",
            "is_deleted_for_everyone",
            "is_edited",
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


class EditMessageSerializer(serializers.ModelSerializer):
    message = serializers.CharField(allow_blank=False)
    message_type = serializers.ChoiceField(
        choices=Message.Types.choices,
        default=Message.Types.TEXT,
    )

    class Meta:
        model = Message
        fields = ("message", "message_type")

    def validate(self, attrs):
        message: Message = cast(Message, self.instance)  # Type hint for better code readability

        if timezone.now() - message.created_at > timedelta(
            seconds=ChatConstants.Message.MessageEdition.EDITABLE_DURATION
        ):
            raise serializers.ValidationError(
                f"You can only edit messages within {ChatConstants.Message.MessageEdition.EDITABLE_DURATION} seconds of sending."
            )

        # Get the requesting user and the destination user
        view = self.context.get("view")
        user: User | None = view.request.user if view and view.request else None

        if not user:
            raise serializers.ValidationError("Authentication credentials were not provided.")

        # Ensure that the message is not deleted for everyone
        if message.is_deleted_for_everyone:
            raise serializers.ValidationError(
                "You cannot edit a message that has been deleted for everyone."
            )

        attrs["user"] = user

        return attrs

    def update(self, instance, validated_data):
        new_message_content = validated_data["message"]
        user = validated_data["user"]

        if instance.message == new_message_content:
            return {
                "status": ResponseStatus.SUCCESS,
                "message": "No changes were made to the message.",
            }

        MessageService().edit_message(
            message=instance,
            user=user,
            new_message_content=new_message_content,
            new_message_type=validated_data["message_type"],
        )

        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Message edited successfully.",
        }

    def to_representation(self, instance):
        return instance


class RepliedMessageSnapshotSerializer(serializers.ModelSerializer):
    sender = NestedRestrictedUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "message",
            "message_type",
            "version",
            "created_at",
            "is_deleted_for_everyone",
            "deleted_for_everyone_at",
            "is_edited",
            "edited_at",
        )
        read_only_fields = fields


# Serializers for WebSocket events
class SendMessageEventPayloadSerializer(serializers.ModelSerializer):
    conversation_id = serializers.UUIDField(write_only=True, source="conversation.id")
    sender = NestedRestrictedUserSerializer(read_only=True)
    message_id = serializers.UUIDField(read_only=True, source="id")
    replied_to = NestedRepliedMessageSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "conversation_id",
            "sender",
            "message_id",
            "message",
            "message_type",
            "created_at",
            "replied_to",
            "replied_message_snapshot",
            "status",
            "is_pinned",
            "is_deleted_for_everyone",
            "is_edited",
        )
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Intial state for a new message
        representation["status"] = MessageStatus.StatusChoices.SENT
        representation["is_pinned"] = False
        representation["reactions"] = []

        return representation
