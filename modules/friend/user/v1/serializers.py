from rest_framework import serializers

from modules.friend.models import Friend
from modules.user.serializers import NestedUserSerializer


class ListFriendSerializer(serializers.ModelSerializer):
    friend = NestedUserSerializer(read_only=True)

    class Meta:
        model = Friend
        fields = ("id", "friend", "created_at")
        read_only_fields = fields
