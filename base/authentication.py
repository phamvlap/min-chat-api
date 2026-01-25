import uuid

import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from base.decorators import retry
from modules.user.models import User
from services.clerk_service import ClerkService


class ClerkAuthentication(BaseAuthentication):
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
            user_data: dict = self._verify_clerk_token(token)
        except Exception as e:
            raise AuthenticationFailed(f"Invalid Clerk token. Error: {str(e)}")

        # Get user ID from the token claims
        user_id: str | None = user_data.get("sub")
        if not user_id:
            raise AuthenticationFailed("Invalid Clerk token: missing user ID.")

        # Retrieve the user by user ID from the Clerk
        clerk_service = ClerkService()

        clerk_user: dict | None = clerk_service.retrieve_user(user_id)
        if not clerk_user:
            raise AuthenticationFailed("Clerk user not found.")

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

    @retry(max_retries=3, delay=1.0, backoff=2)
    def _verify_clerk_token(self, token: str) -> dict:
        # Create a JWKS client from the Clerk JWKS URL
        jwks_client = jwt.PyJWKClient(settings.CLERK_JWKS_URL)

        # Get the signing key for the token
        unverified_header: dict = jwt.get_unverified_header(token)
        signing_key: str = jwks_client.get_signing_key_from_jwt(token).key

        # Decode and verify the token
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=[unverified_header["alg"]],
            issuer=settings.CLERK_ISSUER,
        )

        return claims
