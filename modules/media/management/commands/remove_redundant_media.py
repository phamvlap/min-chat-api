from django.core.management.base import BaseCommand

from modules.media.models import Media
from services.s3_service import S3Service
from utils.upload_utils import get_bucket_name


class Command(BaseCommand):
    def handle(self, *args, **options):
        s3_service = S3Service()
        bucket_name = get_bucket_name(public=True)

        # Get all media object keys from S3
        all_media_objects = s3_service.list_objects(bucket_name)
        media_object_keys: set[str] = {obj["Key"] for obj in all_media_objects}

        # Get all media keys from the database
        media_keys: set[str] = set(Media.objects.values_list("key", flat=True))

        # Identify redundant media keys that exist in the database but not in S3
        redundant_media_keys: set[str] = media_keys - media_object_keys

        if redundant_media_keys:
            # Delete redundant media records from the database
            deleted_count, _ = Media.objects.filter(key__in=redundant_media_keys).delete()
            self.stdout.write(
                self.style.SUCCESS(f"Deleted {deleted_count} redundant media records.")
            )
        else:
            self.stdout.write(self.style.SUCCESS("No redundant media records found."))
