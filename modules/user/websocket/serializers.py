from rest_framework import serializers


class AcknowledgmentSerializer(serializers.Serializer):
    event_dispatch_id = serializers.UUIDField()
