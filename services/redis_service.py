from collections.abc import Awaitable
from inspect import isawaitable
from typing import Any

import orjson
import redis
from django.conf import settings


class RedisClient:
    _client: redis.Redis | None = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        if cls._client is None:
            cls._client = redis.Redis.from_url(settings.REDIS_URL)
        return cls._client


class RedisService:
    def __init__(self):
        self.client = RedisClient.get_client()

    def _ensure_sync_result[T](self, result: Awaitable[T] | T) -> T:
        if isawaitable(result):
            raise RuntimeError(
                "RedisService expects a synchronous redis client, but got an awaitable result."
            )
        return result

    def ping(self) -> bool:
        try:
            return self._ensure_sync_result(self.client.ping())
        except redis.RedisError:
            return False

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        key_parts = (
            [prefix] + [str(arg) for arg in args] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        )
        return ":".join(key_parts)

    def set(self, key: str, value: Any, ttl: int = 300) -> Any:
        data = orjson.dumps(value)
        return self._ensure_sync_result(self.client.set(key, data, ex=ttl))

    def get(self, key: str) -> Any | None:
        value = self._ensure_sync_result(self.client.get(key))
        return orjson.loads(value) if value else None

    def delete(self, key: str) -> Any:
        return self._ensure_sync_result(self.client.delete(key))

    def exists(self, key: str) -> bool:
        return self._ensure_sync_result(self.client.exists(key)) > 0

    def hash_set(self, name: str, key: str, value: Any) -> int:
        data = orjson.dumps(value).decode("utf-8")
        return self._ensure_sync_result(self.client.hset(name, key, data))

    def hash_get(self, name: str, key: str) -> Any | None:
        value = self._ensure_sync_result(self.client.hget(name, key))
        return orjson.loads(value) if value else None

    def hash_delete(self, name: str, key: str) -> int:
        return self._ensure_sync_result(self.client.hdel(name, key))

    def hash_exists(self, name: str, key: str) -> bool:
        return self._ensure_sync_result(self.client.hexists(name, key))

    def hash_get_all(self, name: str) -> dict[str, Any]:
        raw_data: dict = self._ensure_sync_result(self.client.hgetall(name))
        return {k.decode(): orjson.loads(v) for k, v in raw_data.items()}

    def set_add(self, name: str, *values) -> int:
        data = [orjson.dumps(value) for value in values]
        return self._ensure_sync_result(self.client.sadd(name, *data))

    def set_members(self, name: str):
        raw_members = self._ensure_sync_result(self.client.smembers(name))
        return {orjson.loads(member) for member in raw_members}

    def set_remove(self, name: str, *values) -> int:
        data = [orjson.dumps(value) for value in values]
        return self._ensure_sync_result(self.client.srem(name, *data))

    def set_exists(self, name: str, value: Any) -> int:
        data = orjson.dumps(value).decode("utf-8")
        return self._ensure_sync_result(self.client.sismember(name, data))

    def left_push(self, key: str, value: Any) -> int:
        data = orjson.dumps(value)
        return self._ensure_sync_result(self.client.lpush(key, data))

    def right_push(self, key: str, value: Any) -> int:
        data = orjson.dumps(value)
        return self._ensure_sync_result(self.client.rpush(key, data))

    def left_pop(self, key: str) -> str | list | None:
        value: str | list | None = self._ensure_sync_result(self.client.lpop(key))

        if value is not None:
            if isinstance(value, str):
                return orjson.loads(value)

            if isinstance(value, list):
                return [orjson.loads(item) for item in value]

        return None

    def right_pop(self, key: str) -> str | list | None:
        value: str | list | None = self._ensure_sync_result(self.client.rpop(key))

        if value is not None:
            if isinstance(value, str):
                return orjson.loads(value)

            if isinstance(value, list):
                return [orjson.loads(item) for item in value]
        return None

    def list_range(self, key: str, start: int = 0, end: int = -1) -> list[Any]:
        raw_values = self._ensure_sync_result(self.client.lrange(key, start, end))
        return [orjson.loads(value) for value in raw_values]

    def expire(self, key: str, ttl: int):
        return self.client.expire(key, ttl)

    def ttl(self, key: str) -> int:
        return self._ensure_sync_result(self.client.ttl(key))

    def increment(self, key: str, amount: int = 1) -> int:
        return self._ensure_sync_result(self.client.incr(key, amount))

    def decrement(self, key: str, amount: int = 1) -> int:
        return self._ensure_sync_result(self.client.decr(key, amount))

    def flushdb(self):
        return self.client.flushdb()
