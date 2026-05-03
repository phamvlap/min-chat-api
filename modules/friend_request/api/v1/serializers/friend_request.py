from rest_framework import serializers

from base.constants import FriendRequestAction, ResponseStatus
from base.exceptions import (
    AuthenticationCredentialsNotProvidedException,
    FriendAlreadyExistsException,
    FriendRequestAlreadyExistsException,
    FriendRequestSentToSelfException,
)
from modules.friend.services import FriendService
from modules.friend_request.models import FriendRequest
from modules.friend_request.services import FriendRequestService
from modules.user.api.v1.serializers.user import NestedPublicUserSerializer
from modules.user.models import User


class CreateFriendRequestSerializer(serializers.ModelSerializer):
    friend_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_user=True, is_active=True, deleted_at=None),
    )

    class Meta:
        model = FriendRequest
        fields = ("friend_id",)

    def validate(self, attrs):
        view = self.context.get("view")
        user: User | None = view.request.user if view and view.request else None
        friend: User = attrs.pop("friend_id")

        if not user:
            raise AuthenticationCredentialsNotProvidedException()

        if user.id == friend.id:
            raise FriendRequestSentToSelfException()

        if FriendService().are_users_friends(user, friend):
            raise FriendAlreadyExistsException()

        existing_request = FriendRequestService().get_friend_request(sender=user, receiver=friend)
        if existing_request:
            raise FriendRequestAlreadyExistsException()

        attrs["sender"] = user
        attrs["receiver"] = friend

        return attrs

    def create(self, validated_data):
        friend_request = super().create(validated_data)
        return RetrieveFriendRequestSerializer(friend_request).data

    def to_representation(self, instance):
        return instance


class ListFriendRequestSerializer(serializers.ModelSerializer):
    sender = NestedPublicUserSerializer(read_only=True)
    receiver = NestedPublicUserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ("id", "sender", "receiver", "status", "created_at", "responded_at")
        read_only_fields = fields


class RetrieveFriendRequestSerializer(serializers.ModelSerializer):
    sender = NestedPublicUserSerializer(read_only=True)
    receiver = NestedPublicUserSerializer(read_only=True)

    class Meta:
        model = FriendRequest
        fields = ("id", "sender", "receiver", "status", "created_at", "responded_at")
        read_only_fields = fields


class CancelFriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = ()

    def validate(self, attrs):
        view = self.context.get("view")
        user: User | None = view.request.user if view and view.request else None

        attrs["user"] = user

        return attrs

    def update(self, instance, validated_data):
        FriendRequestService().cancel_friend_request(
            user=validated_data["user"],
            friend_request=instance,
        )
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
        action: str = view.kwargs.get("action") if view and view.kwargs else ""
        user: User | None = view.request.user if view and view.request else None

        attrs["action"] = action
        attrs["user"] = user

        return super().validate(attrs)

    def update(self, instance, validated_data):
        FriendRequestService().accept_or_reject_friend_request(
            user=validated_data["user"],
            friend_request=instance,
            action=FriendRequestAction(validated_data["action"]),
        )
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Friend request processed successfully.",
        }

    def to_representation(self, instance):
        return instance
