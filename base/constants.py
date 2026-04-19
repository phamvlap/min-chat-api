from enum import StrEnum
from typing import ClassVar


class ViewAction(StrEnum):
    CREATE = "create"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"


class FriendRequestAction(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"


class WebSocket:
    class ClientEvent:
        class Message(StrEnum):
            SEND_MESSAGE = "send_message"
            MESSAGE_DELIVERED = "message_delivered"

    class ServerEvent:
        class Message(StrEnum):
            MESSAGE = "chat_message"
            MESSAGE_DELIVERED = "chat_message_delivered"
            MESSAGE_PINNED = "chat_message_pinned"
            MESSAGE_UNPINNED = "chat_message_unpinned"
            MESSAGE_DELETED_FOR_EVERYONE = "chat_message_deleted_for_everyone"
            REACTION_UPDATED = "chat_reaction_updated"

    class Group(StrEnum):
        USER = "user.{user_id}"
        CONVERSATION = "conversation.{conversation_id}"

    class ACKConfig:
        MAX_RETRIES = 5
        ACK_TIMEOUT = 5  # 5 seconds


class UploadConstants:
    FILE_OPTIONS: ClassVar[dict[str, str]] = {
        "DOCUMENT": "DOCUMENT",
        "VIDEO": "VIDEO",
        "IMAGE": "IMAGE",
        "AUDIO": "AUDIO",
    }

    VALID_IMAGE_FILE_EXTENSIONS: ClassVar[list[str]] = [
        ".jpg",
        ".png",
        ".webp",
        ".jpeg",
        ".svg",
    ]

    VALID_VIDEO_FILE_EXTENSIONS: ClassVar[list[str]] = [
        ".mp4",
        ".avi",
        ".flv",
        ".mov",
        ".mpeg",
        ".3gp",
        ".wmv",
    ]

    VALID_AUDIO_FILE_EXTENSIONS: ClassVar[list[str]] = [
        ".mp3",
        ".m4a",
    ]

    VALID_DOCUMENT_EXTENSIONS: ClassVar[list[str]] = [
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".csv",
    ]

    VALID_FILE_EXTENSIONS: ClassVar[list[str]] = [
        *VALID_IMAGE_FILE_EXTENSIONS,
        *VALID_VIDEO_FILE_EXTENSIONS,
        *VALID_DOCUMENT_EXTENSIONS,
        *VALID_AUDIO_FILE_EXTENSIONS,
    ]

    TOTAL_IMAGE_EXTENSIONS: ClassVar[list[str]] = [
        ".jpg",
        ".jpeg",
        ".jpe",
        ".jif",
        ".jfif",
        ".jfi",
        ".png",
        ".gif",
        ".webp",
        ".tiff",
        ".tif",
        ".psd",
        ".raw",
        ".arw",
        ".cr2",
        ".nrw",
        ".k25",
        ".bmp",
        ".dib",
        ".heif",
        ".heic",
        ".ind",
        ".indd",
        ".indt",
        ".jp2",
        ".j2k",
        ".jpf",
        ".jpx",
        ".jpm",
        ".mj2",
        ".svg",
        ".svgz",
        ".ai",
        ".eps",
    ]

    TOTAL_VIDEO_EXTENSIONS: ClassVar[list[str]] = [
        ".webm",
        ".mkv",
        ".vob",
        ".ogv",
        ".ogg",
        ".drc",
        ".gifv",
        ".mng",
        ".avi",
        ".MTS",
        ".M2TS",
        ".TS",
        ".mov",
        ".qt",
        ".wmv",
        ".yuv",
        ".rm",
        ".rmvb",
        ".viv",
        ".asf",
        ".amv",
        ".mp4",
        ".m4p",
        ".mpg",
        ".mp2",
        ".f4b",
        ".mpe",
        ".mpv",
        ".mpeg",
        ".m4v",
        ".svi",
        ".3gp",
        ".3g2",
        ".mxf",
        ".roq",
        ".nsv",
        ".flv",
        ".f4v",
        ".f4p ",
        ".f4a",
    ]

    TOTAL_DOCUMENT_EXTENSIONS: ClassVar[list[str]] = [
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        ".odp",
        ".pdf",
        ".xps",
        ".txt",
        ".rtf",
        ".md",
        ".tex",
        ".ltx",
        ".epub",
        ".mobi",
        ".azw",
        ".azw3",
        ".csv",
        ".tsv",
        ".xml",
        ".json",
        ".yaml",
        ".yml",
        ".pages",
        ".log",
    ]

    TOTAL_AUDIO_EXTENSIONS: ClassVar[list[str]] = [
        ".mp3",
        ".wav",
        ".aac",
        ".flac",
        ".alac",
        ".ogg",
        ".oga",
        ".wma",
        ".m4a",
        ".opus",
        ".amr",
        ".aiff",
        ".aif",
        ".aifc",
        ".mka",
        ".mid",
        ".midi",
        ".rmi",
        ".mpa",
        ".mp2",
        ".3gp",
        ".3g2",
        ".webm",
    ]


class TimeConstants:
    ONE_SECOND = 1
    ONE_MINUTE = 60 * ONE_SECOND
    ONE_HOUR = 60 * ONE_MINUTE
    ONE_DAY = 24 * ONE_HOUR
    ONE_WEEK = 7 * ONE_DAY


class ChatConstants:
    class Conversation:
        class Direct:
            class SystemMessage:
                class ConversationStarted(StrEnum):
                    EVENT_NAME = "conversation_started"
                    MESSAGE = "You have started a conversation with {recipient_name}."

    class Message:
        class ReactionStatus(StrEnum):
            ADDED = "added"
            REMOVED = "removed"
