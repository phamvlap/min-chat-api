from rest_framework import serializers

from base.constants import ResponseStatus
from base.exceptions import (
    AuthenticationCredentialsNotProvidedException,
    ConversationIDRequiredInURLException,
    ConversationNotFoundException,
    MessageNotFoundException,
)
from modules.chat.models import Message, MessageReaction
from modules.chat.services import ConversationService, MessageReactionService, MessageService
from modules.user.api.v1.serializers.user import NestedRestrictedUserSerializer
from modules.user.models import User


class MessageReactionInMessageListSerializer(serializers.ModelSerializer):
    reaction_type = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)

    class Meta:
        model = MessageReaction
        fields = ("reaction_type", "count")
        read_only_fields = fields


class ReactMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.UUIDField(write_only=True)
    reaction_type = serializers.ChoiceField(choices=MessageReaction.ReactionTypes.choices)

    class Meta:
        model = MessageReaction
        fields = ("message_id", "reaction_type")

    def validate(self, attrs):
        view = self.context.get("view")
        conversation_id = view.kwargs.get("conversation_id") if view else None

        if not conversation_id:
            raise ConversationIDRequiredInURLException()

        # Validate that the conversation exists and is not deleted
        conversation = ConversationService().get_conversation_by_id(conversation_id)
        if not conversation:
            raise ConversationNotFoundException()

        # Validate that the message exists in the conversation and is not deleted
        message_id = attrs.pop("message_id")
        message = MessageService().get_message_in_conversation(message_id, conversation_id)

        if not message:
            raise MessageNotFoundException()

        attrs["message"] = message

        return attrs

    def create(self, validated_data):
        message: Message = validated_data.pop("message")
        reaction_type: str = validated_data.pop("reaction_type")
        view = self.context.get("view")
        user: User | None = view.request.user if view and view.request else None

        if not user:
            raise AuthenticationCredentialsNotProvidedException()

        reaction_status = MessageReactionService().toggle_reaction(user, message, reaction_type)

        return {
            "status": ResponseStatus.SUCCESS,
            "reaction_status": reaction_status,
        }

    def to_representation(self, instance):
        return instance


class ListMessageReactionSerializer(serializers.ModelSerializer):
    user = NestedRestrictedUserSerializer(read_only=True)

    class Meta:
        model = MessageReaction
        fields = ("id", "user", "reaction_type", "created_at")
        read_only_fields = fields
