import logging
from typing import cast

import redis.asyncio as redis

logger = logging.getLogger("redis")


class RedisClient:
    """Async Redis client wrapper."""

    def __init__(
        self,
        host: str,
        port: int = 6379,
        db: int = 0,
        password: str | None = None,
        decode_responses: bool = True,
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self._client: redis.Redis | None = None
        self._decode_responses = decode_responses

    async def connect(self) -> None:
        """Initialize Redis connection. Failure is non-fatal — client stays None."""
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=self._decode_responses,
            )
            await self._client.ping()
            logger.info("Redis connected: %s:%s", self.host, self.port)
        except Exception as e:
            logger.warning("Redis connection failed: %s. Caching disabled.", e)
            self._client = None

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            logger.info("Redis disconnected")

    async def get(self, key: str) -> str | None:
        if not self._client:
            return None
        return cast(str | None, await self._client.get(key))

    async def set(self, key: str, value: str, expire: int | None = None) -> None:
        if not self._client:
            return
        await self._client.set(key, value, ex=expire)

    async def delete(self, key: str) -> None:
        if not self._client:
            return
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        if not self._client:
            return False
        return await self._client.exists(key) > 0

    async def publish(self, channel: str, message: str) -> None:
        if not self._client:
            return
        await self._client.publish(channel, message)

    async def ping(self) -> bool:
        if not self._client:
            return False
        try:
            return await self._client.ping()
        except Exception:
            return False
