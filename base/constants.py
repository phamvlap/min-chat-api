from enum import Enum


class ViewAction(str, Enum):
    CREATE = "create"
    RETRIEVE = "retrieve"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"


class FriendRequestAction(str, Enum):
    ACCEPT = "accept"
    REJECT = "reject"
