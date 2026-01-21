from django.db import models

from base.models import BaseModel


class Friend(BaseModel):
    user = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="user_friend")
    friend = models.ForeignKey("user.User", on_delete=models.CASCADE, related_name="friend")

    class Meta:
        unique_together = ("user", "friend")
