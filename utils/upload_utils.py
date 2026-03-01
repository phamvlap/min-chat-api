import uuid


def generate_s3_key(file_type: str, file_name: str) -> str:
    """Generate S3 object key"""
    unique_identifier = str(uuid.uuid4()).replace("-", "")
    return f"{file_type.lower()}/{unique_identifier}-{file_name}"
