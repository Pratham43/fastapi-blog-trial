from abc import ABC, abstractmethod
import redis.asyncio as redis
from app.config import settings
from app.core.logging import get_logger

logger = get_logger("cache")

class BaseCache(ABC):
    """Abstract Base Class for Cache Providers (Redis, Valkey, Memcached, etc.)"""
    
    @abstractmethod
    def init(self) -> None:
        """Initialize the cache client."""
        pass
        
    @abstractmethod
    async def close(self) -> None:
        """Close connection to cache."""
        pass

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Retrieve a string value from the cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: str, expire: int = 300) -> None:
        """Save a key-value pair with a TTL in seconds."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Remove a specific key from the cache."""
        pass

    @abstractmethod
    async def clear_pattern(self, pattern: str) -> None:
        """Remove all keys matching a glob pattern."""
        pass


class RedisCacheAdapter(BaseCache):
    """Redis/Valkey Cache Adapter utilizing async redis-py client."""
    
    def __init__(self) -> None:
        self.client: redis.Redis | None = None

    def init(self) -> None:
        if settings.redis_url:
            logger.info("Initializing Redis/Valkey cache adapter", url=settings.redis_url)
            self.client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def close(self) -> None:
        if self.client:
            logger.info("Closing Redis/Valkey cache connection")
            await self.client.close()
            self.client = None

    async def get(self, key: str) -> str | None:
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.warning("Cache GET failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: str, expire: int = 300) -> None:
        if not self.client:
            return
        try:
            await self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.warning("Cache SET failed", key=key, error=str(e))

    async def delete(self, key: str) -> None:
        if not self.client:
            return
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.warning("Cache DELETE failed", key=key, error=str(e))

    async def clear_pattern(self, pattern: str) -> None:
        if not self.client:
            return
        try:
            # Note: KEYS command is fine for simple patterns in small databases. 
            # In production with massive datasets, SCAN is preferred.
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
                logger.info("Cleared cache pattern", pattern=pattern, count=len(keys))
        except Exception as e:
            logger.warning("Cache clear_pattern failed", pattern=pattern, error=str(e))


# Global Cache instance - can be swapped with another provider subclassing BaseCache
cache: BaseCache = RedisCacheAdapter()
