from django.db.models import Count, IntegerField, OuterRef, Prefetch, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce

from base.permission import IsUser
from base.views import BaseCreateAPIView, BaseListAPIView
from modules.chat.models import Conversation, ConversationMember, MessageStatus
from modules.user.models import User

from .serializers import CreateDirectConversationSerializer, ListConversationSerializer


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
        user: User = self.request.user

        # Subquery to count unread messages for each conversation
        unread_message_count_query: QuerySet = (
            MessageStatus.objects.filter(
                user=user,
                deleted_at=None,
                message__conversation=OuterRef("id"),
                created_at__gt=OuterRef("conversation_member__last_read_at"),
            )
            .exclude(
                status=MessageStatus.StatusChoices.READ,
                message__sender=user,
            )
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
            .select_related("owner", "last_message")
            .prefetch_related(
                Prefetch(
                    "conversation_member",
                    queryset=ConversationMember.objects.filter(deleted_at=None).select_related(
                        "user",
                        "last_visible_message",
                    ),
                )
            )
        )
