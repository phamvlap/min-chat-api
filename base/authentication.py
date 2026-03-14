import uuid
from typing import Any
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from utils.clerk_utils import ClerkUtils


class BaseClerkAuthentication:
    def get_or_create_user(self, user_id: str) -> Any | None:
        return self._get_or_create_user(user_id)

    @database_sync_to_async
    def async_get_or_create_user(self, user_id: str) -> Any | None:
        return self._get_or_create_user(user_id)

    def _get_or_create_user(self, user_id: str) -> Any | None:
        # Lazy import to ensure Django settings are fully loaded
        from services.caching_service import UserCachingService
        from services.clerk_service import ClerkService

        User = get_user_model()

        # Initialize the user caching service
        user_caching_service = UserCachingService()

        # Generate cache key for the user
        cache_key: str = user_caching_service.generate_user_cache_key(user_id)

        # Check if the user is cached
        user = user_caching_service.get(cache_key)

        # Return cached user if found
        if user:
            return user

        clerk_service = ClerkService()

        # Retrieve user data from Clerk
        clerk_user: dict | None = clerk_service.retrieve_user(user_id)
        if not clerk_user:
            return None

        # Prepare user data
        username: str = clerk_user["username"] if clerk_user.get("username") else f"user_{user_id}"
        first_name: str = clerk_user["first_name"] if clerk_user.get("first_name") else ""
        last_name: str = clerk_user["last_name"] if clerk_user.get("last_name") else ""
        email: str = (
            clerk_user["email_addresses"][0]["email_address"]
            if clerk_user.get("email_addresses")
            else ""
        )
        unsafe_metadata: dict = clerk_user.get("unsafe_metadata", {})

        # Get or create the user in the database
        user, _ = User.objects.get_or_create(
            clerk_user_id=user_id,
            deleted_at=None,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "is_active": True,
                "clerk_user_id": user_id,
                "password": make_password(str(uuid.uuid4())),
                "is_user": unsafe_metadata.get("is_user", False),
            },
        )

        # Cache the user for future requests
        user_caching_service.set(cache_key, user, timeout=300)

        return user


class ClerkAuthentication(BaseAuthentication, BaseClerkAuthentication):
    """
    Custom authentication class to authenticate users using Clerk tokens.
    """

    def authenticate(self, request):
        # Extract the Clerk token from the Authorization header
        auth_header: str | None = request.headers.get("Authorization", None)

        # No token provided or invalid format
        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # No authentication provided

        # Extract the token
        token: str = auth_header.split(" ")[1]

        # Verify the token and retrieve user data
        try:
            user_data: dict = ClerkUtils.verify_token(token)
        except Exception as e:
            raise AuthenticationFailed(f"Invalid Clerk token. Error: {e!s}") from e

        # Get user ID from the token claims
        user_id: str | None = user_data.get("sub")
        if not user_id:
            raise AuthenticationFailed("Invalid Clerk token: missing user ID.")

        # Retrieve or create the user
        user: Any | None = self.get_or_create_user(user_id)

        if not user:
            raise AuthenticationFailed("User not found or could not be created.")

        return (user, token)


class ClerkAuthMiddleware(BaseMiddleware, BaseClerkAuthentication):
    """
    Custom middleware to authenticate WebSocket connections using Clerk tokens.
    """

    async def __call__(self, scope, receive, send):
        # Extract the query string from the scope
        query_string: str = scope.get("query_string", b"").decode("utf-8")
        query_params: dict[str, list[str]] = parse_qs(query_string)

        # Get the Clerk token from the query parameters
        token_list: list[str] = query_params.get("token", [])
        if not token_list:
            scope["user"] = None
            return await super().__call__(scope, receive, send)

        # Get the first token (if multiple are provided)
        token: str = token_list[0]

        # Verify the token and retrieve user data
        try:
            user_data: dict = ClerkUtils.verify_token(token)
        except Exception:
            scope["user"] = None
            return await super().__call__(scope, receive, send)

        # Get user ID from the token claims
        user_id: str | None = user_data.get("sub")
        if not user_id:
            scope["user"] = None
            return await super().__call__(scope, receive, send)

        # Retrieve or create the user asynchronously
        user: Any | None = await self.async_get_or_create_user(user_id)

        scope["user"] = user
        return await super().__call__(scope, receive, send)
