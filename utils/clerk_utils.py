import jwt
from django.conf import settings

from base.decorators import retry


class ClerkUtils:
    @staticmethod
    @retry(max_retries=3, delay=1.0, backoff=2)
    def verify_token(token: str) -> dict:
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
