from .constants import FriendRequestAction


class FriendRequestActionConverter:
    regex = f"({'|'.join([action.value for action in FriendRequestAction])})"

    # Using for incoming URL to Python
    def to_python(self, value):
        return FriendRequestAction(value)

    # Using for outgoing Python to URL (e.g., reverse function)
    def to_url(self, value):
        return value
