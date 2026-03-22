import os
import uuid

from django.conf import settings
from django.utils.text import slugify


def normalize_file_name(file_name: str) -> str:
    """Normalize file name by slugifying the name and preserving the extension"""

    if file_name.startswith(".") and file_name.count(".") == 1:
        # Handle hidden files (e.g., .env)
        return file_name

    name, ext = os.path.splitext(file_name)
    return f"{slugify(name)}{ext.lower()}"


def generate_s3_key(file_type: str, file_name: str) -> str:
    """Generate S3 object key"""

    new_file_name = normalize_file_name(file_name)
    unique_identifier = uuid.uuid4().hex

    return f"{file_type.lower()}/{unique_identifier}-{new_file_name}"


def get_bucket_name(*, public: bool = True) -> str:
    """Get S3 bucket name based on public flag"""

    return str(settings.S3_PUBLIC_BUCKET) if public else str(settings.S3_PRIVATE_BUCKET)


def build_public_url(key: str) -> str:
    """Build public URL for the given bucket name and key"""

    return f"{settings.SUPABASE_PROJECT_URL}/storage/v1/object/public/{settings.S3_PUBLIC_BUCKET}/{key}"
