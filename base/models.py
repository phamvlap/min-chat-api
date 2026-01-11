import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    created_by = models.UUIDField(null=True)

    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    modified_by = models.UUIDField(null=True)

    deleted_at = models.DateTimeField(default=None, null=True)
    deleted_by = models.UUIDField(null=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["deleted_at"]),
            models.Index(fields=["id", "deleted_at"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_active", "deleted_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["-created_at"]),
        ]


class AbstractBaseUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    # Not used password field of Abstract User
    password = models.CharField(max_length=256, null=True)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    created_by = models.UUIDField(null=True)

    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    modified_by = models.UUIDField(null=True)

    deleted_at = models.DateTimeField(default=None, null=True)
    deleted_by = models.UUIDField(null=True)

    objects = UserManager()

    class Meta:
        abstract = True
