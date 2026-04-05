from typing import Any

import jwt
from django.conf import settings

from base.constants import TimeConstants
from base.decorators import retry


def get_jwks_client():
    from services.caching_service import CachingService

    # Generate a cache key for the JWKS client
    jwks_client_cache_key = "authentication:clerk_jwks_client"

    caching_service = CachingService()

    # Try to get the JWKS client from the cache
    jwks_client = caching_service.get(jwks_client_cache_key)

    # If the JWKS client is found in the cache, return it
    if jwks_client:
        return jwks_client

    # Create a new JWKS client if it's not found in the cache
    jwks_client = jwt.PyJWKClient(str(settings.CLERK_JWKS_URL))

    # Cache the JWKS client for 24 hours to avoid fetching it on every authentication request
    caching_service.set(jwks_client_cache_key, jwks_client, timeout=24 * TimeConstants.ONE_HOUR)

    return jwks_client


class ClerkUtils:
    @staticmethod
    @retry(max_retries=3, delay=1.0, backoff=2)
    def verify_token(token: str) -> dict:
        jwks_client = get_jwks_client()

        # Get the signing key for the token
        unverified_header: dict = jwt.get_unverified_header(token)
        signing_key: Any = jwks_client.get_signing_key_from_jwt(token).key

        # Decode and verify the token
        return jwt.decode(
            token,
            signing_key,
            algorithms=[unverified_header["alg"]],
            issuer=settings.CLERK_ISSUER,
        )
