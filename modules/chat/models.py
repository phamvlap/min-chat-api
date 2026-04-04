from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import BaseModel


class Conversation(BaseModel):
    class Types(models.TextChoices):
        DIRECT = "direct", _("Direct")
        GROUP = "group", _("Group")

    type = models.CharField(max_length=10, choices=Types.choices, default=Types.DIRECT)

    # The last message in the conversation
    last_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
        default=None,
    )
    last_message_at = models.DateTimeField(null=True, blank=True, default=None)

    # Fields for group conversation
    title = models.CharField(max_length=256, blank=True, null=True, default=None)
    avatar = models.ForeignKey(
        "media.Media",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        default=None,
    )
    owner = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="owner_conversation",
        null=True,
        default=None,
    )


class ConversationMember(BaseModel):
    class MemberRoles(models.TextChoices):
        OWNER = "owner", _("Owner")
        ADMIN = "admin", _("Admin")
        MEMBER = "member", _("Member")

    # The conversation to which the member belongs
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="conversation_member",
    )

    # The user who is a member of the conversation
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="user_conversation_member",
    )

    # Role of the member in the conversation
    role = models.CharField(max_length=10, choices=MemberRoles.choices, default=MemberRoles.MEMBER)

    # Mute settings
    muted_until = models.DateTimeField(null=True, blank=True, default=None)

    # Timestamp of the last read message
    last_read_at = models.DateTimeField(auto_now=False, auto_now_add=True)

    # Last visible message for the user
    last_visible_message = models.ForeignKey(
        "Message",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
        default=None,
    )


class Message(BaseModel):
    class Types(models.TextChoices):
        TEXT = "text", _("Text")
        IMAGE = "image", _("Image")
        VIDEO = "video", _("Video")
        AUDIO = "audio", _("Audio")
        DOCUMENT = "document", _("Document")
        SYSTEM = "system", _("System")

    # The conversation to which the message belongs
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="conversation_message",
    )

    # The user who sent the message
    sender = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="sent_messages",
        null=True,
    )

    # The content and type of the message
    message = models.TextField(blank=True, null=True, default=None)
    message_type = models.CharField(max_length=10, choices=Types.choices, default=Types.TEXT)

    # Reference to another message if this is a reply
    replied_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="replied_to_message",
        null=True,
        blank=True,
        default=None,
    )


class MessageStatus(BaseModel):
    class StatusChoices(models.TextChoices):
        SENT = "sent", _("Sent")
        DELIVERED = "delivered", _("Delivered")
        READ = "read", _("Read")

    # The message whose status is being tracked
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="message_status")

    # The user for whom the status applies
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="user_message_status",
    )

    # The status of the message for the user
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.SENT,
    )
