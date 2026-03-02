from rest_framework import serializers

from modules.media.models import Media


class NestedMediaInRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = (
            "id",
            "key",
            "key_type",
            "original_name",
            "file_size",
            "public",
            "public_url",
        )
        read_only_fields = fields


class NestedMediaInCreateAndUpdateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()

    class Meta:
        model = Media
        fields = ("id",)
