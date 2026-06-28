from rest_framework.permissions import BasePermission


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.deleted_at is None
        )


class IsUser(IsAuthenticated):
    """
    Allows access only to regular authenticated users.
    """

    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_user


class BaseWebsocketPermission:
    """
    A base class from which all websocket permission classes should inherit.
    """

    def has_permission(self, scope) -> bool:
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return True


class IsWebsocketAuthenticated(BaseWebsocketPermission):
    """
    Allows access only to authenticated websocket users.
    """

    def has_permission(self, scope) -> bool:
        user = scope.get("user")
        return user and user.is_authenticated and user.is_active and user.deleted_at is None


class IsWebsocketUser(IsWebsocketAuthenticated):
    """
    Allows access only to regular authenticated websocket users.
    """

    def has_permission(self, scope) -> bool:
        return super().has_permission(scope) and scope["user"].is_user
