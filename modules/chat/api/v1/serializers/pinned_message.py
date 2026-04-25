from rest_framework import serializers

from base.constants import ResponseStatus, WebSocket
from modules.chat.api.v1.serializers.message import NestedMessageSerializer
from modules.chat.models import PinnedMessage
from modules.chat.services import ConversationService, MessageService, PinnedMessageService
from modules.event_dispatch.services import EventDispatchService
from modules.user.models import User
from modules.user.serializers import NestedPublicUserSerializer, NestedRestrictedUserSerializer


class ListPinnedMessageSerializer(serializers.ModelSerializer):
    message = NestedMessageSerializer(read_only=True)

    class Meta:
        model = PinnedMessage
        fields = ("id", "message", "created_at")
        read_only_fields = fields

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Get context data for mapped creators
        mapped_creators: dict = self.context.get("mapped_creators", {})

        # Retrieve the creator information from the mapped creators using the created_by field
        creator = mapped_creators.get(str(instance.created_by))

        # Add creator information to the representation if available
        representation["creator"] = (
            NestedRestrictedUserSerializer(creator).data if creator else None
        )

        return representation


class RetrievePinnedMessageSerializer(serializers.ModelSerializer):
    message = NestedMessageSerializer(read_only=True)

    class Meta:
        model = PinnedMessage
        fields = ("id", "message", "created_at")
        read_only_fields = fields


class PinMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = PinnedMessage
        fields = ("message_id",)

    def validate(self, attrs):
        view = self.context.get("view")
        conversation_id = view.kwargs.get("conversation_id") if view else None
        user: User | None = view.request.user if view and view.request else None

        if not conversation_id:
            raise serializers.ValidationError("Conversation ID is required in the URL.")

        # Validate that the conversation exists and is not deleted
        conversation = ConversationService().get_conversation_by_id(conversation_id)
        if not conversation:
            raise serializers.ValidationError("Conversation not found.")

        # Validate that the message exists in the conversation and is not deleted
        message_id = attrs.pop("message_id")
        message = MessageService().get_message_in_conversation(message_id, conversation_id)

        if not message:
            raise serializers.ValidationError("Message not found in the specified conversation.")

        # Validate the message is pinned in the conversation
        if PinnedMessageService().get_pinned_message_in_conversation(message_id, conversation_id):
            raise serializers.ValidationError("Message is already pinned in this conversation.")

        attrs["conversation"] = conversation
        attrs["message"] = message
        attrs["created_by"] = str(user.id) if user else None

        return attrs

    def create(self, validated_data):
        # Create the pinned message instance
        pinned_message = super().create(validated_data)

        # Serialize the pinned message data
        serialized_data = RetrievePinnedMessageSerializer(pinned_message).data

        # Add creator information to the serialized data
        creator = (
            User.objects.filter(id=pinned_message.created_by, deleted_at=None)
            .select_related("avatar")
            .first()
        )
        serialized_data["creator"] = NestedPublicUserSerializer(creator).data if creator else None

        # Dispatch the pinned message event to the conversation group via Channels
        EventDispatchService().dispatch_event(
            entity=pinned_message,
            event_type=WebSocket.ServerEvent.Message.MESSAGE_PINNED,
            payload=serialized_data,
            group_name=WebSocket.Group.CONVERSATION.format(
                conversation_id=pinned_message.conversation.id
            ),
        )

        return serialized_data

    def to_representation(self, instance):
        return instance


class UnpinMessageSerializer(serializers.ModelSerializer):
    message_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = PinnedMessage
        fields = ("message_id",)

    def validate(self, attrs):
        view = self.context.get("view")
        conversation_id = view.kwargs.get("conversation_id") if view else None

        if not conversation_id:
            raise serializers.ValidationError("Conversation ID is required in the URL.")

        # Validate that the conversation exists and is not deleted
        conversation = ConversationService().get_conversation_by_id(conversation_id)
        if not conversation:
            raise serializers.ValidationError("Conversation not found.")

        # Validate that the message exists in the conversation and is not deleted
        message_id = attrs.pop("message_id")
        message = MessageService().get_message_in_conversation(message_id, conversation_id)

        if not message:
            raise serializers.ValidationError("Message not found in the specified conversation.")

        pinned_message = PinnedMessageService().get_pinned_message_in_conversation(
            message_id,
            conversation_id,
            select_related_fields=("message", "conversation"),
        )
        # Validate the message is pinned in the conversation
        if not pinned_message:
            raise serializers.ValidationError("Message is not pinned in this conversation.")

        attrs["pinned_message"] = pinned_message

        return attrs

    def create(self, validated_data):
        pinned_message: PinnedMessage = validated_data.pop("pinned_message")
        PinnedMessageService().unpin_message(pinned_message)

        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Message unpinned successfully.",
        }

    def to_representation(self, instance):
        return instance
