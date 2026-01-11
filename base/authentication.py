import uuid

import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from modules.user.models import User
from services.clerk_service import ClerkService


class ClerkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Extract the Clerk token from the Authorization header
        auth_header: str | None = request.headers.get("Authorization", None)

        if not auth_header or not auth_header.startswith("Bearer "):
            return None  # No authentication provided

        token: str = auth_header.split(" ")[1]

        user_data: dict | None = self._verify_clerk_token(token)

        if not user_data:
            raise AuthenticationFailed("Invalid Clerk token.")

        user_id: str | None = user_data.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Invalid Clerk token: missing user ID.")

        clerk_service = ClerkService()
        clerk_user: dict | None = clerk_service.retrieve_user(user_id)
        if not clerk_user:
            raise AuthenticationFailed("Clerk user not found.")

        username: str = clerk_user["username"] if clerk_user.get("username") else f"user_{user_id}"
        first_name: str = clerk_user["first_name"] if clerk_user.get("first_name") else ""
        last_name: str = clerk_user["last_name"] if clerk_user.get("last_name") else ""
        email: str = (
            clerk_user["email_addresses"][0]["email_address"]
            if clerk_user.get("email_addresses")
            else ""
        )
        unsafe_metadata: dict = clerk_user.get("unsafe_metadata", {})

        user, created = User.objects.get_or_create(
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

        return (user, token)

    def _verify_clerk_token(self, token: str) -> dict | None:
        try:
            jwks_client = jwt.PyJWKClient(settings.CLERK_JWKS_URL)
            unverified_header = jwt.get_unverified_header(token)
            signing_key = jwks_client.get_signing_key(unverified_header["kid"]).key
            claims = jwt.decode(token, signing_key, [unverified_header["alg"]])
            return claims
        except Exception:
            return None
