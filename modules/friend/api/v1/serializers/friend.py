from rest_framework import serializers

from modules.friend.models import Friend
from modules.user.api.v1.serializers.user import NestedRestrictedUserSerializer


class ListFriendSerializer(serializers.ModelSerializer):
    friend = NestedRestrictedUserSerializer(read_only=True)

    class Meta:
        model = Friend
        fields = ("id", "friend", "created_at")
        read_only_fields = fields


class RetrieveFriendSerializer(serializers.ModelSerializer):
    friend = NestedRestrictedUserSerializer(read_only=True)

    class Meta:
        model = Friend
        fields = ("id", "friend", "created_at")
        read_only_fields = fields
