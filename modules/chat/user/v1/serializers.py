from django.db.models import Count
from rest_framework import serializers

from modules.chat.models import Conversation, ConversationMember, Message
from modules.user.models import User
from modules.user.serializers import NestedUserSerializer


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
        user: User = self.context.get("view").request.user
        destination_user: User = attrs.pop("destination_user_id")

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
        ConversationMember.objects.bulk_create(
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
            "owner",
            "last_message",
            "last_message_at",
            "members",
            "created_at",
            "unread_message_count",
        )
        read_only_fields = fields


class RetrieveConversationSerializer(serializers.ModelSerializer):
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
    replied_to = NestedMessageSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "message", "message_type", "created_at", "replied_to")
        read_only_fields = fields


class NestedMessageSerializer(serializers.ModelSerializer):
    sender = NestedUserSerializer(read_only=True)
    replied_to = NestedMessageSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "message", "message_type", "created_at", "replied_to")
        read_only_fields = fields


class ReadMessageSerializer(serializers.Serializer):
    read_before = serializers.DateTimeField()


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False)
    message_type = serializers.ChoiceField(
        choices=Message.Types.choices,
        default=Message.Types.TEXT,
    )


class BuildPayloadMessageSerializer(serializers.Serializer):
    type = serializers.CharField()
    conversation_id = serializers.UUIDField()
    sender_id = serializers.UUIDField()
    message_id = serializers.UUIDField()
    message = serializers.CharField()
    message_type = serializers.CharField()
    created_at = serializers.DateTimeField()
