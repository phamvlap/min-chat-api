from rest_framework import serializers

from modules.chat.models import Message


class DeliverMessageSerializer(serializers.Serializer):
    delivered_before = serializers.DateTimeField()


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(allow_blank=False)
    message_type = serializers.ChoiceField(
        choices=Message.Types.choices,
        default=Message.Types.TEXT,
    )
