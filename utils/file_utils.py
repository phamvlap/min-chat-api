import mimetypes

from base.constants import UploadConstants
from modules.media.models import Media


def get_file_extension(file_name: str) -> str:
    return f".{file_name.split('.')[-1].lower()}" if "." in file_name else ""


def get_file_type_from_extension(file_extension: str) -> str | None:
    total_file_extension_map: dict[str, list[str]] = {
        Media.KeyTypes.IMAGE: UploadConstants.TOTAL_IMAGE_EXTENSIONS,
        Media.KeyTypes.VIDEO: UploadConstants.TOTAL_VIDEO_EXTENSIONS,
        Media.KeyTypes.DOCUMENT: UploadConstants.TOTAL_DOCUMENT_EXTENSIONS,
        Media.KeyTypes.AUDIO: UploadConstants.TOTAL_AUDIO_EXTENSIONS,
    }

    for file_type, extensions in total_file_extension_map.items():
        if file_extension in extensions:
            return file_type

    return None


def guess_mime_type(file_name: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_name)
    if not mime_type:
        return "application/octet-stream"
    return mime_type
