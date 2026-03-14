from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from base.constants import FriendRequestAction, ResponseStatus
from modules.friend.models import Friend
from modules.friend_request.models import FriendRequest
from modules.user.models import User
from modules.user.serializers import NestedUserSerializer


class CreateFriendRequestSerializer(serializers.ModelSerializer):
    friend_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_user=True, is_active=True, deleted_at=None),
    )

    class Meta:
        model = FriendRequest
        fields = ("friend_id",)

    def validate(self, attrs):
        view = self.context.get("view")
        user: User = view.request.user
        friend: User = attrs.pop("friend_id")

        if user.id == friend.id:
            raise serializers.ValidationError("You cannot send a friend request to yourself.")

        is_friend: bool = Friend.objects.filter(
            (Q(user=user, friend=friend) | Q(user=friend, friend=user)),
            deleted_at=None,
        ).exists()
        if is_friend:
            raise serializers.ValidationError("You are already friends with this user.")

        existing_request: FriendRequest | None = FriendRequest.objects.filter(
            (Q(sender=user, receiver=friend) | Q(sender=friend, receiver=user)),
            deleted_at=None,
            status__in=FriendRequest.exclude_statuses_on_creation(),
        ).first()
        if existing_request:
            raise serializers.ValidationError(
                "A friend request already exists between you and this user."
            )

        attrs["sender"] = user
        attrs["receiver"] = friend

        return attrs

    def create(self, validated_data):
        friend_request = super().create(validated_data)
        return RetrieveFriendRequestSerializer(friend_request).data

    def to_representation(self, instance):
        return instance


class ListFriendRequestSerializer(serializers.ModelSerializer):
    sender = NestedUserSerializer(read_only=True)
    receiver = NestedUserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ("id", "sender", "receiver", "status", "created_at", "responded_at")
        read_only_fields = fields


class RetrieveFriendRequestSerializer(serializers.ModelSerializer):
    sender = NestedUserSerializer(read_only=True)
    receiver = NestedUserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ("id", "sender", "receiver", "status", "created_at", "responded_at")
        read_only_fields = fields


class CancelFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ()

    def validate(self, attrs):
        attrs["status"] = FriendRequest.Status.CANCELED
        return attrs

    def update(self, instance, validated_data):
        super().update(instance, validated_data)
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Friend request canceled successfully.",
        }

    def to_representation(self, instance):
        return instance


class AcceptOrRejectFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ()

    def validate(self, attrs):
        view = self.context.get("view")
        action = view.kwargs.get("action")

        action_to_status_map = {
            FriendRequestAction.ACCEPT: FriendRequest.Status.ACCEPTED,
            FriendRequestAction.REJECT: FriendRequest.Status.REJECTED,
        }

        try:
            attrs["status"] = action_to_status_map[action]
        except KeyError:
            raise serializers.ValidationError("Invalid action for friend request.")

        attrs["responded_at"] = timezone.now()

        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if instance.status == FriendRequest.Status.ACCEPTED:
            # Create friendship in both directions
            Friend.objects.bulk_create(
                [
                    Friend(user=instance.sender, friend=instance.receiver),
                    Friend(user=instance.receiver, friend=instance.sender),
                ]
            )
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Friend request processed successfully.",
        }

    def to_representation(self, instance):
        return instance
