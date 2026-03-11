from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from base.constants import TimeConstants, UploadConstants
from modules.media.models import Media
from services.s3_service import S3Service
from templates.error_templates import ErrorTemplate
from utils.file_utils import get_file_extension, get_file_type_from_extension
from utils.upload_utils import generate_s3_key, get_bucket_name


class BaseUploadMediaSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=256)
    file_type = serializers.ChoiceField(choices=Media.KeyTypes.choices)
    file_size = serializers.FloatField(min_value=0, default=0)
    public = serializers.BooleanField(default=False)

    def validate_file_extension(self, file_name: str, file_type: str | None) -> str:
        file_extension: str = get_file_extension(file_name)

        # Map of valid file extensions for each file type
        valid_file_extension_map: dict[str, list[str]] = {
            Media.KeyTypes.IMAGE: UploadConstants.VALID_IMAGE_FILE_EXTENSIONS,
            Media.KeyTypes.VIDEO: UploadConstants.VALID_VIDEO_FILE_EXTENSIONS,
            Media.KeyTypes.DOCUMENT: UploadConstants.VALID_DOCUMENT_EXTENSIONS,
            Media.KeyTypes.AUDIO: UploadConstants.VALID_AUDIO_FILE_EXTENSIONS,
        }

        if file_type:
            valid_extensions: list[str] = valid_file_extension_map.get(file_type, [])
            # If there are valid extensions for the given file type, check if the file extension is valid
            if valid_extensions and file_extension not in valid_extensions:
                raise ValidationError(
                    ErrorTemplate.UploadError.invalid_file_extension(valid_extensions)
                )

            # If the file type is provided and valid, but the extension is not in the overall valid list
            if file_extension not in UploadConstants.VALID_FILE_EXTENSIONS:
                """If does not pass the file_type, check what type it is"""
                detected_file_type: str | None = get_file_type_from_extension(file_extension)

                raise ValidationError(
                    ErrorTemplate.UploadError.invalid_file_extension(
                        valid_file_extension_map.get(
                            detected_file_type, UploadConstants.VALID_FILE_EXTENSIONS
                        )
                    )
                )
        return file_extension

    def validate(self, attrs):
        self.validate_file_extension(file_name=attrs["file_name"], file_type=attrs["file_type"])
        return attrs

    def to_representation(self, instance):
        return instance


class CreatePresignedURLSerializer(BaseUploadMediaSerializer):
    def create(self, validated_data):
        # Generate S3 key
        key: str = generate_s3_key(
            file_type=validated_data["file_type"],
            file_name=validated_data["file_name"],
        )

        # Generate presigned URL
        bucket_name: str = get_bucket_name(public=validated_data["public"])
        presigned_url = S3Service().generate_presigned_url(
            bucket_name=bucket_name,
            method="put",
            params={"key": key},
            expires_in=5 * TimeConstants.ONE_MINUTE,
        )

        # Create media record
        media = Media.objects.create(
            key=key,
            key_type=validated_data["file_type"],
            original_name=validated_data["file_name"],
            file_size=validated_data["file_size"],
            public=validated_data["public"],
        )
        return {"presigned_url": presigned_url, "key": key, "id": media.id}


class GetPresignedURLSerializer(serializers.Serializer):
    key = serializers.CharField()

    def create(self, validated_data):
        media: Media = Media.objects.filter(key=validated_data["key"], deleted_at=None).first()
        if not media:
            raise ValidationError("Media with the given key does not exist.")

        bucket_name: str = get_bucket_name(public=media.public)

        presigned_url: str = S3Service().generate_presigned_url(
            bucket_name=bucket_name,
            method="get",
            params={"key": validated_data["key"]},
            expires_in=10 * TimeConstants.ONE_MINUTE,  # 10 minutes
        )

        return {"presigned_url": presigned_url}

    def to_representation(self, instance):
        return instance


class CreateMultipartUploadSerializer(BaseUploadMediaSerializer):
    def create(self, validated_data):
        # Generate S3 key
        key: str = generate_s3_key(
            file_type=validated_data["file_type"],
            file_name=validated_data["file_name"],
        )

        # Create multipart upload and get upload ID
        bucket_name: str = get_bucket_name(public=validated_data["public"])
        upload_id: str = S3Service().create_multipart_upload(
            bucket_name=bucket_name,
            key=key,
            expires_in=5 * TimeConstants.ONE_MINUTE,
        )

        # Create media record
        Media.objects.create(
            key=key,
            key_type=validated_data["file_type"],
            original_name=validated_data["file_name"],
            file_size=validated_data["file_size"],
            public=validated_data["public"],
            is_active=False,  # Mark as inactive until the multipart upload is completed
        )
        return {"upload_id": upload_id, "key": key}


class GetPresignedURLForMultipartUploadSerializer(serializers.Serializer):
    upload_id = serializers.CharField()
    key = serializers.CharField()
    part_no = serializers.IntegerField()

    def create(self, validated_data):
        media: Media = Media.objects.filter(key=validated_data["key"], deleted_at=None).first()
        if not media:
            raise ValidationError("Media with the given key does not exist.")

        bucket_name: str = get_bucket_name(public=media.public)

        presigned_url: str = S3Service().generate_presigned_url_for_multipart_upload(
            bucket_name=bucket_name,
            key=validated_data["key"],
            upload_id=validated_data["upload_id"],
            part_no=validated_data["part_no"],
        )

        return {"presigned_url": presigned_url}

    def to_representation(self, instance):
        return instance


class MultipartUploadChunkSerializer(serializers.Serializer):
    ETag = serializers.CharField()
    PartNumber = serializers.IntegerField()


class CompleteMultipartUploadSerializer(serializers.Serializer):
    upload_id = serializers.CharField()
    key = serializers.CharField()
    parts = MultipartUploadChunkSerializer(many=True)

    def create(self, validated_data):
        media: Media = Media.objects.filter(key=validated_data["key"], deleted_at=None).first()
        if not media:
            raise ValidationError("Media with the given key does not exist.")

        bucket_name: str = get_bucket_name(public=media.public)

        S3Service().complete_multipart_upload(
            bucket_name=bucket_name,
            key=validated_data["key"],
            upload_id=validated_data["upload_id"],
            parts=validated_data["parts"],
        )

        # Mark media as active after successful completion of multipart upload
        media.is_active = True
        media.save(update_fields=["is_active"])

        return {
            "id": media.id,
            "key": media.key,
            "message": "Multipart upload completed successfully.",
        }

    def to_representation(self, instance):
        return instance
