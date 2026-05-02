from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import BaseModel


class EventDispatch(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        ACKED = "acked", _("Acknowledged")
        FAILED = "failed", _("Failed")

    # Generic relation to any entity that is object of the event
    entity_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    entity_id = models.UUIDField()
    entity = GenericForeignKey("entity_content_type", "entity_id")

    # Event details
    event_type = models.CharField(max_length=256)
    payload = models.JSONField()
    group_name = models.CharField(max_length=256)

    # Retry mechanism
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    max_retries = models.PositiveIntegerField(default=5)
    retry_count = models.PositiveIntegerField(default=0)
    last_attempted_at = models.DateTimeField(null=True, blank=True, default=None)

    # Acknowledgment mechanism
    ack_deadline_at = models.DateTimeField(null=True, blank=True, default=None)
    acked_at = models.DateTimeField(null=True, blank=True, default=None)

    def is_acknowledged(self) -> bool:
        return self.acked_at is not None and self.status == self.Status.ACKED

    def is_terminal(self) -> bool:
        return self.status in {self.Status.ACKED, self.Status.FAILED}

    def is_retry_exhausted(self) -> bool:
        return self.retry_count >= self.max_retries

    def mark_as_failed(self) -> None:
        self.status = self.Status.FAILED
        self.save(update_fields=["status"])
