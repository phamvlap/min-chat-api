import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)

    # Not used password field of Abstract User
    password = models.CharField(max_length=256, null=True)

    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    created_by = models.UUIDField(null=True)

    modified_at = models.DateTimeField(auto_now=True, auto_now_add=False, null=True)
    modified_by = models.UUIDField(null=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(default=None, null=True)
    deleted_by = models.UUIDField(null=True)

    username = models.CharField(max_length=256, unique=True, null=True, blank=True)

    # Email
    email = models.EmailField()
