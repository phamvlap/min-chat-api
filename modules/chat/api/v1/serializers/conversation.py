from rest_framework import serializers

from modules.chat.api.v1.serializers.member import NestedConversationMemberSerializer
from modules.chat.models import Conversation
from modules.chat.services import ConversationService
from modules.media.serializers import NestedMediaInRetrieveSerializer
from modules.user.api.v1.serializers.user import NestedRestrictedUserSerializer
from modules.user.models import User

from .message import NestedMessageSerializer


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
        existing_conversation: Conversation | None = ConversationService().get_direct_conversation(
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

        return ConversationService().create_direct_conversation(user, destination_user)


class ListConversationSerializer(serializers.ModelSerializer):
    avatar = NestedMediaInRetrieveSerializer(read_only=True)
    owner = NestedRestrictedUserSerializer(read_only=True)
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
    owner = NestedRestrictedUserSerializer(read_only=True)
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
