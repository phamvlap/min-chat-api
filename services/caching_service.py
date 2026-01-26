from typing import Any

from cacheops import CacheMiss, cache


class CachingService:
    def __init__(self):
        self.cache = cache

    def get(self, key: str) -> Any | None:
        try:
            return self.cache.get(key)
        except CacheMiss:
            return None

    def set(self, key: str, data: Any, timeout: int = 300) -> None:
        self.cache.set(key, data, timeout=timeout)

    def delete(self, key: str) -> None:
        self.cache.delete(key)

    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key based on a prefix and additional arguments.

        Args:
            prefix (str): The prefix for the cache key.
            *args: Additional positional arguments to include in the key.
            **kwargs: Additional keyword arguments to include in the key.

        Returns:
            The generated cache key as a string.
        """
        key_parts = (
            [prefix] + [str(arg) for arg in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        )
        return ":".join(key_parts)


class UserCachingService(CachingService):
    def generate_user_cache_key(self, user_id: str) -> str:
        return self.generate_cache_key("user", id=user_id)
