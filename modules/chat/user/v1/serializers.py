import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Count
from rest_framework import serializers

from base.constants import ChatConstants, ResponseStatus, WebSocket
from modules.chat.models import (
    Conversation,
    ConversationMember,
    Message,
    MessageStatus,
    PinnedMessage,
)
from modules.media.serializers import NestedMediaInRetrieveSerializer
from modules.user.models import User
from modules.user.serializers import NestedUserSerializer
from utils.normalizer_utils import to_serializable_dict


class CreateDirectConversationSerializer(serializers.ModelSerializer):
    destination_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(deleted_at=None),
        write_only=True,
    )

    class Meta:
        model = Conversation
        fields = ("id", "destination_user_id")

    def validate(self, attrs):
        # Get the requesting user and the destination user
        view = self.context.get("view")
        user: User | None = view.request.user if view and view.request else None
        destination_user: User = attrs.pop("destination_user_id")

        if not user:
            raise serializers.ValidationError("Authentication credentials were not provided.")

        # Prevent users from creating a conversation with themselves
        if user.id == destination_user.id:
            raise serializers.ValidationError(
                "You cannot create a direct conversation with yourself."
            )

        # Check for an existing direct conversation between the two users
        existing_conversation: Conversation | None = self._get_existing_conversation(
            user,
            destination_user,
        )

        attrs["user"] = user
        attrs["destination_user"] = destination_user
        attrs["existing_conversation"] = existing_conversation

        return attrs

    def create(self, validated_data):
        # If an existing conversation is found, return it
        existing_conversation: Conversation | None = validated_data.pop("existing_conversation")
        if existing_conversation:
            return existing_conversation

        # Create a new direct conversation
        user: User = validated_data.pop("user")
        destination_user: User = validated_data.pop("destination_user")

        validated_data["type"] = Conversation.Types.DIRECT
        conversation: Conversation = super().create(validated_data)

        # Add both users as members of the conversation
        members = ConversationMember.objects.bulk_create(
            [
                ConversationMember(
                    conversation=conversation,
                    user=user,
                    role=ConversationMember.MemberRoles.MEMBER,
                ),
                ConversationMember(
                    conversation=conversation,
                    user=destination_user,
                    role=ConversationMember.MemberRoles.MEMBER,
                ),
            ]
        )

        # Define the content of the first system message for the conversation
        first_message_content = {
            "event": ChatConstants.Conversation.Direct.SystemMessage.ConversationStarted.EVENT_NAME,
            "content": ChatConstants.Conversation.Direct.SystemMessage.ConversationStarted.MESSAGE.format(
                recipient_name=destination_user.full_name
            ),
        }

        message_data: dict = {
            "conversation": conversation,
            "sender": None,
            "message": json.dumps(first_message_content),
            "message_type": Message.Types.SYSTEM,
        }

        # Create the first system message for the conversation
        message: Message = Message.objects.create(**message_data)

        # Create message status for each member
        message_statuses: list[MessageStatus] = []
        for member in members:
            message_status: MessageStatus = MessageStatus(
                message=message,
                user=member.user,
                status=MessageStatus.StatusChoices.SENT,
            )
            message_statuses.append(message_status)

        # Bulk create message statuses
        MessageStatus.objects.bulk_create(message_statuses)

        # Update the last message in the conversation
        conversation.last_message = message
        conversation.last_message_at = message.created_at
        conversation.save(update_fields=["last_message", "last_message_at"])

        # Update last visible message for each member
        ConversationMember.objects.filter(
            conversation=conversation,
            deleted_at=None,
        ).update(last_visible_message=message)

        return conversation

    def _get_existing_conversation(self, user: User, destination_user: User) -> Conversation | None:
        return (
            Conversation.objects.filter(
                type=Conversation.Types.DIRECT,
                conversation_member__user__in=[user, destination_user],
            )
            .annotate(member_count=Count("conversation_member"))
            .filter(member_count=2)
            .first()
        )


class NestedMessageSerializer(serializers.ModelSerializer):
    sender = NestedUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "message", "message_type", "created_at")
        read_only_fields = fields


class NestedConversationMemberSerializer(serializers.ModelSerializer):
    user = NestedUserSerializer(read_only=True)
    last_visible_message = NestedMessageSerializer(read_only=True)

    class Meta:
        model = ConversationMember
        fields = ("id", "user", "role", "muted_until", "last_read_at", "last_visible_message")
        read_only_fields = fields


class ListConversationSerializer(serializers.ModelSerializer):
    avatar = NestedMediaInRetrieveSerializer(read_only=True)
    owner = NestedUserSerializer(read_only=True)
    members = NestedConversationMemberSerializer(
        many=True,
        read_only=True,
        source="conversation_member",
    )
    last_message = NestedMessageSerializer(read_only=True)
    unread_message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "type",
            "title",
            "avatar",
            "owner",
            "last_message",
            "last_message_at",
            "members",
            "created_at",
            "unread_message_count",
        )
        read_only_fields = fields


class RetrieveConversationSerializer(serializers.ModelSerializer):
    avatar = NestedMediaInRetrieveSerializer(read_only=True)
    owner = NestedUserSerializer(read_only=True)
    members = NestedConversationMemberSerializer(
        many=True,
        read_only=True,
        source="conversation_member",
    )
    last_message = NestedMessageSerializer(read_only=True)
    unread_message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Conversation
        fields = (
            "id",
            "type",
            "title",
            "avatar",
            "owner",
            "last_message",
            "last_message_at",
            "members",
            "created_at",
            "unread_message_count",
        )
        read_only_fields = fields


class ListMessageSerializer(serializers.ModelSerializer):
    sender = NestedUserSerializer(read_only=True)
    replied_to = "self"  # Recursive relationship for nested replies
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "message", "message_type", "created_at", "replied_to", "status")
        read_only_fields = fields


class ReadMessageSerializer(serializers.Serializer):
    read_before = serializers.DateTimeField()


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False)
    message_type = serializers.ChoiceField(
        choices=Message.Types.choices,
        default=Message.Types.TEXT,
    )


class DeliverMessageSerializer(serializers.Serializer):
    delivered_before = serializers.DateTimeField()


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
        representation["creator"] = NestedUserSerializer(creator).data if creator else None

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

        # Validate that the conversation exists and is not deleted
        conversation = Conversation.objects.filter(id=conversation_id, deleted_at=None).first()
        if not conversation:
            raise serializers.ValidationError("Conversation not found.")

        # Validate that the message exists in the conversation and is not deleted
        message_id = attrs.pop("message_id")
        message = Message.objects.filter(
            id=message_id,
            conversation=conversation,
            deleted_at=None,
        ).first()

        if not message:
            raise serializers.ValidationError("Message not found in the specified conversation.")

        # Validate the message is pinned in the conversation
        if PinnedMessage.objects.filter(
            conversation=conversation,
            message=message,
            deleted_at=None,
        ).exists():
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
        creator = User.objects.filter(id=pinned_message.created_by).select_related("avatar").first()
        serialized_data["creator"] = NestedUserSerializer(creator).data if creator else None

        # Send the pinned message data to the conversation group via Channels
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"conversation_{pinned_message.conversation.id}",
            {
                "type": WebSocket.ServerEvent.Message.MESSAGE_PINNED,
                **to_serializable_dict(serialized_data),
            },
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

        # Validate that the conversation exists and is not deleted
        conversation = Conversation.objects.filter(id=conversation_id, deleted_at=None).first()
        if not conversation:
            raise serializers.ValidationError("Conversation not found.")

        # Validate that the message exists in the conversation and is not deleted
        message_id = attrs.pop("message_id")
        message = Message.objects.filter(
            id=message_id,
            conversation=conversation,
            deleted_at=None,
        ).first()

        if not message:
            raise serializers.ValidationError("Message not found in the specified conversation.")

        pinned_message = (
            PinnedMessage.objects.filter(
                conversation=conversation,
                message=message,
                deleted_at=None,
            )
            .select_related("conversation", "message")
            .first()
        )
        # Validate the message is pinned in the conversation
        if not pinned_message:
            raise serializers.ValidationError("Message is not pinned in this conversation.")

        attrs["pinned_message"] = pinned_message

        return attrs

    def create(self, validated_data):
        pinned_message: PinnedMessage = validated_data.pop("pinned_message")

        # Delete the pinned message instance to unpin the message
        pinned_message.delete()

        # Send the unpinned message ID to the conversation group via Channels
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"conversation_{pinned_message.conversation.id}",
            {
                "type": WebSocket.ServerEvent.Message.MESSAGE_UNPINNED,
                "message_id": str(pinned_message.message.id),
            },
        )

        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Message unpinned successfully.",
        }

    def to_representation(self, instance):
        return instance
