import uuid

from django.conf import settings


def generate_s3_key(file_type: str, file_name: str) -> str:
    """Generate S3 object key"""
    unique_identifier = str(uuid.uuid4()).replace("-", "")
    return f"{file_type.lower()}/{unique_identifier}-{file_name}"


def get_bucket_name(*, public: bool = True) -> str:
    """Get S3 bucket name based on public flag"""

    return settings.S3_PUBLIC_BUCKET if public else settings.S3_PRIVATE_BUCKET


def build_public_url(key: str) -> str:
    """Build public URL for the given bucket name and key"""

    return f"{settings.SUPABASE_PROJECT_URL}/storage/v1/object/public/{settings.S3_PUBLIC_BUCKET}/{key}"
