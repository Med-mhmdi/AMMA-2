import json

import redis

from app.config import settings


class CacheService:
    """Redis cache integration for analytics responses."""

    def __init__(self):
        self.client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

    @staticmethod
    def get_cache_key(user_id: int, key_type: str) -> str:
        return f"analytics:{user_id}:{key_type}"

    def get(self, key: str):
        value = self.client.get(key)
        if value is None:
            return None
        return json.loads(value)

    def set(self, key: str, value, ttl_seconds: int = 120):
        self.client.set(key, json.dumps(value), ex=ttl_seconds)

    def delete(self, key: str):
        self.client.delete(key)