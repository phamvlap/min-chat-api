from uuid import UUID

from services.caching_service import UserCachingService


class UserService:
    def __init__(self):
        pass

    def clear_user_cache(self, user_id: str | UUID) -> None:
        # Clear cache for the updated user
        user_caching_service = UserCachingService()

        # Generate cache key for the user
        cache_key: str = user_caching_service.generate_user_cache_key(str(user_id))
        user_caching_service.delete(cache_key)
