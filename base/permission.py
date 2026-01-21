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
