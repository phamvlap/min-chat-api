from rest_framework import status
from rest_framework.exceptions import APIException


class RetryException(Exception):
    """Custom exception for retry mechanism errors."""


class BaseAPIException(APIException):
    """Base API exception with a default status code and detail message."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "An error occurred while processing your request."
    default_code = "base_error"


class AuthenticationCredentialsNotProvidedException(BaseAPIException):
    default_detail = "Authentication credentials were not provided."
    default_code = "authentication_credentials_not_provided"


class UserNotFoundException(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "User not found."
    default_code = "user_not_found"


class DirectConversationCreatedWithSelfException(BaseAPIException):
    default_detail = "You cannot create a direct conversation with yourself."
    default_code = "direct_conversation_created_with_self"


class ConversationIDRequiredInURLException(BaseAPIException):
    default_detail = "Conversation ID is required in the URL."
    default_code = "conversation_id_required_in_url"


class ConversationNotFoundException(BaseAPIException):
    default_detail = "Conversation not found."
    default_code = "conversation_not_found"


class MessageNotFoundException(BaseAPIException):
    default_detail = "Message not found in the specified conversation."
    default_code = "message_not_found"


class MessageDeletedForEveryoneException(BaseAPIException):
    default_detail = (
        "You cannot perform this action on a message that has been deleted for everyone."
    )
    default_code = "message_deleted_for_everyone"


class MessageEditedOutsideAllowedWindowTimeException(BaseAPIException):
    default_detail = "You cannot edit a message outside the allowed edit window time."
    default_code = "message_edited_outside_allowed_window_time"


class MessageAlreadyPinnedException(BaseAPIException):
    default_detail = "The message is already pinned in this conversation."
    default_code = "message_already_pinned"


class PinnedMessageNotFoundException(BaseAPIException):
    default_detail = "Pinned message not found in the specified conversation."
    default_code = "pinned_message_not_found"


class MessageFromSystemCannotBeDeletedException(BaseAPIException):
    default_detail = "System messages cannot be deleted."
    default_code = "message_from_system_cannot_be_deleted"


class MessageDeletedForEveryoneOnlyBySenderException(BaseAPIException):
    default_detail = "Only the sender can delete a message for everyone."
    default_code = "message_deleted_for_everyone_only_by_sender"


class FriendRequestSentToSelfException(BaseAPIException):
    default_detail = "You cannot send a friend request to yourself."
    default_code = "friend_request_sent_to_self"


class FriendRequestAlreadyExistsException(BaseAPIException):
    default_detail = "A friend request already exists between you and this user."
    default_code = "friend_request_already_exists"


class FriendAlreadyExistsException(BaseAPIException):
    default_detail = "You are already friends with this user."
    default_code = "friend_already_exists"


class MediaDoesNotExistException(BaseAPIException):
    default_detail = "The specified media does not exist."
    default_code = "media_does_not_exist"
