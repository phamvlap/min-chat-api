from rest_framework import serializers


class DeleteMessageSerializer(serializers.Serializer):
    message_id = serializers.UUIDField(write_only=True)
    is_deleted_for_everyone = serializers.BooleanField(default=False, write_only=True)
