import json

from app.utils.cache_handler import redis_client


class CacheService:

    async def get(
        self,
        key: str
    ):
        value = await redis_client.get(key)

        if not value:
            return None

        return json.loads(value)

    async def set(
        self,
        key: str,
        value,
        ttl: int = 300
    ):
        await redis_client.set(
            key,
            json.dumps(value),
            ex=ttl
        )

    async def delete(
        self,
        key: str
    ):
        await redis_client.delete(key)