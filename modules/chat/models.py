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

    class Meta:
        indexes = [
            models.Index(fields=["last_message_at"]),
            models.Index(fields=["last_message_at", "deleted_at"]),
        ]


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

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "user", "deleted_at"]),
        ]


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

    # The current content and type of the message
    message = models.TextField(blank=True, null=True, default=None)
    message_type = models.CharField(max_length=10, choices=Types.choices, default=Types.TEXT)

    # Version field to track edits to the message
    version = models.PositiveIntegerField(default=0)

    # Reference to another message if this is a reply
    replied_to = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="replied_to_message",
        null=True,
        blank=True,
        default=None,
    )
    replied_message_snapshot = models.JSONField(null=True, blank=True, default=None)

    # Flag to indicate if the message has been deleted for everyone
    is_deleted_for_everyone = models.BooleanField(default=False)
    deleted_for_everyone_at = models.DateTimeField(null=True, blank=True, default=None)
    deleted_for_everyone_by = models.ForeignKey(
        "user.User",
        on_delete=models.SET_NULL,
        related_name="deleted_for_everyone_by_message",
        null=True,
        blank=True,
        default=None,
    )

    # Flag to indicate if the message has been edited
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True, default=None)
    edited_by = models.ForeignKey(
        "user.User",
        on_delete=models.SET_NULL,
        related_name="edited_by_message",
        null=True,
        blank=True,
        default=None,
    )

    class Meta:
        indexes = [
            models.Index(fields=["conversation", "created_at", "deleted_at"]),
        ]


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

    class Meta:
        indexes = [
            models.Index(fields=["message", "user", "deleted_at", "status"]),
            models.Index(fields=["user", "created_at", "deleted_at"]),
        ]


class PinnedMessage(BaseModel):
    # The conversation to which the pinned message belongs
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="conversation_pinned_message",
    )

    # The message that is pinned in the conversation
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="message_pinned_message",
    )

    class Meta:
        unique_together = ("conversation", "message")
        indexes = [
            models.Index(fields=["conversation", "deleted_at"]),
        ]


class MessageVisibility(BaseModel):
    # The message whose visibility is being tracked
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="message_visibility",
    )

    # The user for whom the visibility applies
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="user_message_visibility",
    )

    # Flag to indicate if the message is hidden for the user
    is_hidden = models.BooleanField(default=False)
    hidden_at = models.DateTimeField(null=True, blank=True, default=None)


class MessageReaction(BaseModel):
    class ReactionTypes(models.TextChoices):
        HEART = "heart", _("Heart")
        THUMBS_UP = "thumbs_up", _("Thumbs Up")
        THUMBS_DOWN = "thumbs_down", _("Thumbs Down")
        LAUGHING = "laughing", _("Laughing")
        CRY = "cry", _("Cry")
        ANGRY = "angry", _("Angry")

    # The message to which the reaction belongs
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="message_reaction",
    )

    # The user who reacted to the message
    user = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="user_message_reaction",
    )

    # The type of reaction
    reaction_type = models.CharField(max_length=20, choices=ReactionTypes.choices)

    class Meta:
        unique_together = ("message", "user", "reaction_type")


class UserAlias(BaseModel):
    # The conversation member for whom the alias is set
    target_member = models.ForeignKey(
        ConversationMember,
        on_delete=models.CASCADE,
        related_name="target_member_user_alias",
    )

    nickname = models.CharField(max_length=256, blank=True, null=True, default=None)

    # The user who set the alias for the target member
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="user_alias")


class MessageRevision(BaseModel):
    # The message for which the revision is being tracked
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="message_revision",
    )

    # The content of the message at the time of the revision
    message_content = models.TextField(blank=True, null=True, default=None)
    message_type = models.CharField(
        max_length=10,
        choices=Message.Types.choices,
        default=Message.Types.TEXT,
    )

    # The content of the message before the revision (for edit history)
    old_message_content = models.TextField(blank=True, null=True, default=None)
    old_message_type = models.CharField(
        max_length=10,
        choices=Message.Types.choices,
        default=Message.Types.TEXT,
    )

    # The version number of the revision
    version = models.PositiveIntegerField(default=0)
