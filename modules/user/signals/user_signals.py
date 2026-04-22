from django.db.models.signals import post_save
from django.dispatch import receiver

from modules.user.models import User
from modules.user.services import UserService


@receiver(post_save, sender=User)
def user_updated(sender, instance: User, created: bool, **kwargs):  # noqa: ARG001
    # Clear cache for the updated user
    UserService().clear_user_cache(str(instance.clerk_user_id))
