from django.db import models

from base.models import AbstractBaseUser


class User(AbstractBaseUser):
    username = models.CharField(max_length=256, unique=True, null=True, blank=True)

    # Email
    email = models.EmailField()

    # User role
    is_user = models.BooleanField(default=False)

    # Clerk Authentication
    clerk_user_id = models.CharField(max_length=256, unique=True, null=True, blank=True)
