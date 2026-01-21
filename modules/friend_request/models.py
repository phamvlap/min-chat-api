from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import BaseModel


class FriendRequest(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        ACCEPTED = "accepted", _("Accepted")
        REJECTED = "rejected", _("Rejected")

    sender = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="sender_friend_request",
    )
    receiver = models.ForeignKey(
        "user.User",
        on_delete=models.CASCADE,
        related_name="receiver_friend_request",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    responded_at = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        unique_together = ("sender", "receiver", "status")

    @classmethod
    def excluded_discovery_statuses(cls) -> list[Status]:
        return [cls.Status.PENDING, cls.Status.ACCEPTED]
