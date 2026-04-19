from django.db.models import Q
from django.utils import timezone

from base.constants import FriendRequestAction
from modules.friend.models import Friend
from modules.friend_request.models import FriendRequest
from modules.user.models import User


class FriendRequestService:
    def __init__(self):
        pass

    def get_friend_request(self, sender: User, receiver: User) -> FriendRequest | None:
        return FriendRequest.objects.filter(
            (Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)),
            deleted_at=None,
            status__in=FriendRequest.exclude_statuses_on_creation(),
        ).first()

    def accept_or_reject_friend_request(
        self,
        user: User,
        friend_request: FriendRequest,
        action: FriendRequestAction,
    ) -> None:
        action_to_status_map = {
            FriendRequestAction.ACCEPT.value: FriendRequest.Status.ACCEPTED,
            FriendRequestAction.REJECT.value: FriendRequest.Status.REJECTED,
        }

        # Update the status of the friend request based on the action
        friend_request.status = action_to_status_map.get(action.value, friend_request.status)
        friend_request.responded_at = timezone.now()
        friend_request.modified_at = timezone.now()
        friend_request.modified_by = user.id
        friend_request.save(update_fields=["status", "responded_at", "modified_at", "modified_by"])

        # If the friend request was accepted, create a friendship in both directions
        if friend_request.status == FriendRequest.Status.ACCEPTED:
            sender = friend_request.sender
            receiver = friend_request.receiver
            # Create friendship in both directions
            Friend.objects.bulk_create(
                [
                    Friend(user=sender, friend=receiver),
                    Friend(user=receiver, friend=sender),
                ]
            )

    def cancel_friend_request(self, user: User, friend_request: FriendRequest) -> None:
        friend_request.status = FriendRequest.Status.CANCELED
        friend_request.modified_at = timezone.now()
        friend_request.modified_by = user.id
        friend_request.save(update_fields=["status", "modified_at", "modified_by"])
