from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import BaseModel
from utils.upload_utils import build_public_url


class Media(BaseModel):
    class KeyTypes(models.TextChoices):
        IMAGE = "image", _("Image")
        VIDEO = "video", _("Video")
        DOCUMENT = "document", _("Document")
        AUDIO = "audio", _("Audio")
        OTHER = "other", _("Other")

    # The unique key for the media file, which can be used to retrieve it from storage
    key = models.CharField(max_length=256, unique=True)
    key_type = models.CharField(max_length=20, choices=KeyTypes.choices)

    original_name = models.CharField(max_length=256)
    file_size = models.PositiveIntegerField()

    # The configuration of the storage bucket where the media file is stored
    public = models.BooleanField(default=False)

    @property
    def public_url(self) -> str | None:
        if self.public:
            return build_public_url(self.key)

        return None
