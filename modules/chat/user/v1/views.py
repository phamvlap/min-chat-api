from collections import defaultdict
from typing import Any, cast

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import (
    Case,
    CharField,
    Count,
    Exists,
    IntegerField,
    OuterRef,
    Prefetch,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response

from base.constants import ViewAction, WebSocket
from base.permission import IsUser
from base.views import (
    BaseCreateAPIView,
    BaseDestroyAPIView,
    BaseListAPIView,
    BaseRetrieveAPIView,
    BaseUpdateAPIView,
)
from modules.chat.models import (
    Conversation,
    ConversationMember,
    Message,
    MessageReaction,
    MessageStatus,
    MessageVisibility,
    PinnedMessage,
)
from modules.user.models import User

from .filters import ListMessageFilter, ListMessageReactionFilter
from .serializers import (
    CreateDirectConversationSerializer,
    DeleteMessageSerializer,
    ListConversationSerializer,
    ListMessageReactionSerializer,
    ListMessageSerializer,
    ListPinnedMessageSerializer,
    PinMessageSerializer,
    ReactMessageSerializer,
    ReadMessageSerializer,
    RetrieveConversationSerializer,
    UnpinMessageSerializer,
)


class CreateDirectConversationAPIView(BaseCreateAPIView):
    permission_classes = (IsUser,)
    model = Conversation
    serializer_class = CreateDirectConversationSerializer


class ListConversationAPIView(BaseListAPIView):
    permission_classes = (IsUser,)
    model = Conversation
    serializer_class = ListConversationSerializer
    search_fields = ("title",)

    def get_queryset(self):
        user: User = cast(User, self.request.user)

        # Subquery to count unread messages for each conversation
        unread_message_count_query: QuerySet = (
            MessageStatus.objects.filter(
                user=user,
                deleted_at=None,
                message__conversation=OuterRef("id"),
                created_at__gt=OuterRef("conversation_member__last_read_at"),
            )
            .exclude(message__sender=user)
            .exclude(status=MessageStatus.StatusChoices.READ)
            .values("message__conversation")
            .annotate(count=Count("id"))
            .values("count")[:1]
        )

        return (
            super()
            .get_queryset()
            .filter(
                conversation_member__user=user,
                conversation_member__deleted_at=None,
                last_message__isnull=False,
            )
            .annotate(
                unread_message_count=Coalesce(
                    Subquery(unread_message_count_query, output_field=IntegerField()),
                    Value(0),
                )
            )
            .order_by("-last_message_at")
            .select_related("avatar", "owner__avatar", "last_message__sender__avatar")
            .prefetch_related(
                Prefetch(
                    "conversation_member",
                    queryset=ConversationMember.objects.filter(deleted_at=None).select_related(
                        "user__avatar",
                        "last_visible_message__sender__avatar",
                    ),
                )
            )
        )


class RetrieveConversationAPIView(BaseRetrieveAPIView):
    permission_classes = (IsUser,)
    model = Conversation
    serializer_class = RetrieveConversationSerializer
    lookup_url_kwarg = "conversation_id"

    def get_queryset(self):
        user: User = cast(User, self.request.user)

        # Subquery to count unread messages for each conversation
        unread_message_count_query: QuerySet = (
            MessageStatus.objects.filter(
                user=user,
                deleted_at=None,
                message__conversation=OuterRef("id"),
                created_at__gt=OuterRef("conversation_member__last_read_at"),
            )
            .exclude(message__sender=user)
            .exclude(status=MessageStatus.StatusChoices.READ)
            .values("message__conversation")
            .annotate(count=Count("id"))
            .values("count")[:1]
        )

        return (
            super()
            .get_queryset()
            .filter(
                conversation_member__user=user,
                conversation_member__deleted_at=None,
                last_message__isnull=False,
            )
            .annotate(
                unread_message_count=Coalesce(
                    Subquery(unread_message_count_query, output_field=IntegerField()),
                    Value(0),
                )
            )
            .order_by("-last_message_at")
            .select_related("avatar", "owner__avatar", "last_message__sender__avatar")
            .prefetch_related(
                Prefetch(
                    "conversation_member",
                    queryset=ConversationMember.objects.filter(deleted_at=None).select_related(
                        "user__avatar",
                        "last_visible_message__sender__avatar",
                    ),
                )
            )
        )


class ListMessageAPIView(BaseListAPIView):
    permission_classes = (IsUser,)
    model = Message
    serializer_class = ListMessageSerializer
    filterset_class = ListMessageFilter

    def get_queryset(self):
        user: User = cast(User, self.request.user)
        conversation_id = self.kwargs.get("conversation_id")

        return (
            super()
            .get_queryset()
            .filter(
                conversation__id=conversation_id,
                conversation__conversation_member__user=user,
                conversation__conversation_member__deleted_at=None,
            )
            .exclude(
                message_visibility__user=user,
                message_visibility__is_hidden=True,
                message_visibility__deleted_at=None,
            )
            .annotate(
                status=Case(
                    When(
                        sender=user,
                        then=Case(
                            When(
                                Exists(
                                    MessageStatus.objects.filter(
                                        message=OuterRef("id"),
                                        status=MessageStatus.StatusChoices.READ,
                                    ).exclude(user=user)
                                ),
                                then=Value(MessageStatus.StatusChoices.READ),
                            ),
                            When(
                                Exists(
                                    MessageStatus.objects.filter(
                                        message=OuterRef("id"),
                                        status=MessageStatus.StatusChoices.DELIVERED,
                                    ).exclude(user=user)
                                ),
                                then=Value(MessageStatus.StatusChoices.DELIVERED),
                            ),
                            default=Value(MessageStatus.StatusChoices.SENT),
                            output_field=CharField(),
                        ),
                    ),
                    default=Value(MessageStatus.StatusChoices.READ),
                    output_field=CharField(),
                ),
                is_pinned=Exists(
                    PinnedMessage.objects.filter(
                        conversation_id=conversation_id,
                        message=OuterRef("id"),
                        deleted_at=None,
                    )
                ),
            )
            .select_related("sender__avatar", "replied_to__sender__avatar")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()

        # Get the message IDs from the queryset and fetch the corresponding reactions
        message_ids = self.get_queryset().values_list("id", flat=True)
        reactions = (
            MessageReaction.objects.filter(message_id__in=message_ids, deleted_at=None)
            .values("message_id", "reaction_type")
            .annotate(count=Count("id"))
        )

        # Create a mapping of message IDs to their reactions and add it to the context
        message_reaction_mapping: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for reaction in reactions:
            message_id = str(reaction["message_id"])
            message_reaction_mapping[message_id].append(
                {
                    "reaction_type": reaction["reaction_type"],
                    "count": reaction["count"],
                }
            )
        context["message_reaction_mapping"] = message_reaction_mapping

        return context


class ReadMessageAPIView(BaseUpdateAPIView):
    permission_classes = (IsUser,)
    model = MessageStatus
    serializer_class = ReadMessageSerializer
    lookup_url_kwarg = "conversation_id"

    def put(self, request, *args, **kwargs):
        # Validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get the read_before timestamp from validated data
        read_before = serializer.validated_data.get("read_before")

        # Get the current user and conversation ID from URL
        user: User = cast(User, self.request.user)
        conversation_id = self.kwargs.get("conversation_id")

        # Update message statuses of messages that are before the read_before timestamp to READ
        read_count: int = (
            MessageStatus.objects.filter(
                user=user,
                message__conversation__id=conversation_id,
                message__created_at__lte=read_before,
                deleted_at=None,
            )
            .exclude(status=MessageStatus.StatusChoices.READ, message__sender=user)
            .update(status=MessageStatus.StatusChoices.READ)
        )

        # Also update the last_read_at timestamp in ConversationMember
        ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user=user,
            deleted_at=None,
        ).update(last_read_at=read_before)

        return Response({"read_count": read_count}, status=status.HTTP_200_OK)


class ListPinMessageAPIView(BaseListAPIView, BaseCreateAPIView):
    permission_classes = (IsUser,)
    model = PinnedMessage
    serializer_class = PinMessageSerializer
    lookup_url_kwarg = "conversation_id"
    ordering_fields = ("created_at", "message__created_at")

    def get_queryset(self):
        user: User = cast(User, self.request.user)

        return (
            super()
            .get_queryset()
            .filter(
                conversation_id=self.kwargs.get("conversation_id"),
                conversation__deleted_at=None,
            )
            .exclude(
                message__message_visibility__user=user,
                message__message_visibility__is_hidden=True,
                message__message_visibility__deleted_at=None,
            )
            .select_related("message__sender__avatar")
        )

    def get_serializer_class(self):
        if self.action == ViewAction.CREATE:
            return PinMessageSerializer
        return ListPinnedMessageSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        # Get the creator IDs from the queryset and fetch the corresponding User objects
        creator_ids = self.get_queryset().values_list("created_by", flat=True).distinct()
        creators = User.objects.filter(id__in=creator_ids, deleted_at=None).select_related("avatar")

        # Create a mapping of creator IDs to User objects and add it to the context
        mapped_creators = {str(creator.id): creator for creator in creators}
        context["mapped_creators"] = mapped_creators

        return context


class UnpinMessageAPIView(BaseCreateAPIView):
    permission_classes = (IsUser,)
    model = PinnedMessage
    serializer_class = UnpinMessageSerializer
    lookup_url_kwarg = "conversation_id"


class DeleteMessageAPIView(BaseDestroyAPIView):
    permission_classes = (IsUser,)
    model = Message
    serializer_class = DeleteMessageSerializer
    lookup_url_kwarg = "conversation_id"

    def get_queryset(self):
        user: User = cast(User, self.request.user)
        conversation_id = self.kwargs.get("conversation_id")

        return (
            super()
            .get_queryset()
            .filter(
                conversation__id=conversation_id,
                conversation__conversation_member__user=user,
                conversation__conversation_member__deleted_at=None,
            )
        )

    def destroy(self, request, *args, **kwargs):
        conversation_id = kwargs.get("conversation_id")
        user = cast(User, self.request.user)

        # Validate that the conversation exists and is not deleted
        conversation = Conversation.objects.filter(id=conversation_id, deleted_at=None).first()
        if not conversation:
            raise serializers.ValidationError("Conversation not found.")

        # Validate request data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get validated data
        validated_data = serializer.validated_data

        # Validate that the message exists in the conversation and is not deleted
        message_id = validated_data.pop("message_id")
        message = (
            Message.objects.filter(
                id=message_id,
                conversation=conversation,
                deleted_at=None,
            )
            .select_related("sender", "conversation")
            .first()
        )

        if not message:
            raise serializers.ValidationError("Message not found in the specified conversation.")

        if not message.sender or message.message_type == Message.Types.SYSTEM:
            raise serializers.ValidationError("System messages cannot be deleted.")

        if validated_data["is_deleted_for_everyone"] and not self._can_delete_for_everyone(
            user,
            message,
        ):
            raise serializers.ValidationError(
                "You can only delete messages for everyone that you have sent."
            )

        # Perform the delete operation
        if validated_data["is_deleted_for_everyone"]:
            # If the message is already deleted for everyone, return 204 No Content without doing anything
            if message.is_deleted_for_everyone:
                return Response(status=status.HTTP_204_NO_CONTENT)

            # Mark the message as deleted for everyone
            message.is_deleted_for_everyone = True
            message.deleted_for_everyone_at = timezone.now()
            message.deleted_for_everyone_by = user
            message.save(
                update_fields=[
                    "is_deleted_for_everyone",
                    "deleted_for_everyone_at",
                    "deleted_for_everyone_by",
                ]
            )

            # Notify all members in the conversation about the message being deleted for everyone
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                WebSocket.Group.CONVERSATION.format(conversation_id=conversation_id),
                {
                    "type": WebSocket.ServerEvent.Message.MESSAGE_DELETED_FOR_EVERYONE,
                    "message_id": str(message.id),
                },
            )
        else:
            # Mark the message as hidden for the user
            MessageVisibility.objects.update_or_create(
                message=message,
                user=user,
                defaults={
                    "is_hidden": True,
                    "hidden_at": timezone.now(),
                },
            )

            # Update the last visible message for the user in the conversation if necessary
            self._update_last_message_for_user(user, message)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update_last_message_for_user(self, user: User, message: Message):
        # Get the ConversationMember instance for the user and conversation
        member = (
            ConversationMember.objects.filter(
                conversation=message.conversation,
                user=user,
                deleted_at=None,
            )
            .select_related("last_visible_message")
            .first()
        )

        # Only update the last visible message if the deleted message is currently the last visible message for the user
        if member and member.last_visible_message == message:
            # Find the new last visible message for the user in the conversation
            new_last_message = self._find_new_last_message(message.conversation, user)

            # Update the last visible message for the user in the conversation
            member.last_visible_message = new_last_message
            member.save(update_fields=["last_visible_message"])

    def _can_delete_for_everyone(self, user: User, message: Message) -> bool:
        return bool(message.sender and message.sender.id == user.id)

    def _find_new_last_message(self, conversation: Conversation, user: User) -> Message | None:
        return (
            Message.objects.filter(
                conversation=conversation,
                conversation__deleted_at=None,
            )
            .exclude(message_visibility__user=user, message_visibility__is_hidden=True)
            .order_by("-created_at")
            .first()
        )


class ReactMessageAPIView(BaseCreateAPIView):
    permission_classes = (IsUser,)
    model = MessageReaction
    serializer_class = ReactMessageSerializer
    lookup_url_kwarg = "conversation_id"


class ListMessageReactionAPIView(BaseListAPIView):
    permission_classes = (IsUser,)
    model = MessageReaction
    serializer_class = ListMessageReactionSerializer
    filterset_class = ListMessageReactionFilter
    lookup_url_kwarg = "conversation_id"

    def get_queryset(self):
        user: User = cast(User, self.request.user)
        conversation_id = self.kwargs.get("conversation_id")
        message_id = self.kwargs.get("message_id")

        return (
            super()
            .get_queryset()
            .filter(
                message__conversation_id=conversation_id,
                message__conversation__deleted_at=None,
                message__conversation__conversation_member__user=user,
                message_id=message_id,
                deleted_at=None,
            )
            .exclude(
                message__message_visibility__user=user,
                message__message_visibility__is_hidden=True,
                message__message_visibility__deleted_at=None,
            )
            .select_related("user__avatar")
        )
