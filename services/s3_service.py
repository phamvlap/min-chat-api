import logging
from typing import Any, Dict, List, Literal

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

from utils.file_utils import guess_mime_type

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            config=Config(
                signature_version="s3v4",
                region_name=settings.S3_REGION,
            ),
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,
        )
        self.method_conversion = {
            "get": "get_object",
            "put": "put_object",
        }

    def generate_presigned_url(
        self,
        bucket_name: str,
        method: Literal["get", "put"],
        params: Dict[str, str | int],
        expires_in: int,
    ) -> str:
        """Generate a presigned S3 URL that can be used to perform an action.

        Args:
            bucket_name: The name of the S3 bucket.
            method: The name of the client method that the URL performs.
            params: The parameters of the specified client method. Must include the `key` parameter for the S3 object.
            expires_in: The number of seconds the presigned URL is valid for.

        Returns:
            The presigned URL.
        """

        try:
            client_action: str = self.method_conversion[method]
            presigned_url: str = self.s3_client.generate_presigned_url(
                ClientMethod=client_action,
                Params={
                    "Bucket": bucket_name,
                    "Key": params["key"],
                },
                ExpiresIn=expires_in,
                HttpMethod="PUT",
            )
            logger.info("Got presigned URL: %s", presigned_url)
        except ClientError:
            logger.exception("Couldn't get a presigned URL for client method '%s'.", method)
            raise
        return presigned_url

    def create_multipart_upload(self, bucket_name: str, key: str, expires_in: int) -> str:
        """Initiate a multipart upload and return the upload ID.

        Args:
            bucket_name: The name of the S3 bucket.
            key: The key of the S3 object to be uploaded.
        Returns:
            The upload ID as a string.
        """
        content_type: str = guess_mime_type(key)

        response = self.s3_client.create_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            Expires=expires_in,
            ContentType=content_type,
        )
        return response["UploadId"]

    def generate_presigned_url_for_multipart_upload(
        self,
        bucket_name: str,
        key: str,
        upload_id: str,
        part_no: int,
    ) -> str:
        """Generate a presigned URL for uploading a part in a multipart upload.

        Args:
            bucket_name: The name of the S3 bucket.
            key: The key of the S3 object to be uploaded.
            upload_id: The upload ID of the multipart upload.
            part_no: The part number of the part to be uploaded.
        Returns:
            The presigned URL as a string.
        """
        presigned_url: str = self.s3_client.generate_presigned_url(
            ClientMethod="upload_part",
            Params={
                "Bucket": bucket_name,
                "Key": key,
                "UploadId": upload_id,
                "PartNumber": part_no,
            },
        )
        return presigned_url

    def complete_multipart_upload(
        self,
        bucket_name: str,
        key: str,
        upload_id: str,
        parts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Complete a multipart upload.

        Args:
            bucket_name: The name of the S3 bucket.
            key: The key of the S3 object to be uploaded.
            upload_id: The upload ID of the multipart upload.
            parts: A list of part dictionaries, each containing `ETag` and `PartNumber`.
        Returns:
            The response after completing the multipart upload.
        """

        response = self.s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            MultipartUpload={"Parts": parts},
            UploadId=upload_id,
        )

        return response
