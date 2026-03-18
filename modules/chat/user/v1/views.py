from typing import cast

from django.db.models import Count, IntegerField, OuterRef, Prefetch, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.response import Response

from base.permission import IsUser
from base.views import BaseCreateAPIView, BaseListAPIView, BaseRetrieveAPIView, BaseUpdateAPIView
from modules.chat.models import Conversation, ConversationMember, Message, MessageStatus
from modules.user.models import User

from .filters import ListMessageFilter
from .serializers import (
    CreateDirectConversationSerializer,
    ListConversationSerializer,
    ListMessageSerializer,
    ReadMessageSerializer,
    RetrieveConversationSerializer,
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
            .select_related("sender__avatar", "replied_to__sender__avatar")
            .order_by("-created_at")
        )


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
