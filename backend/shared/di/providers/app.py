"""
Infrastructure-level Dishka providers.

AppProvider:     creates app-scoped singletons (DB, Redis, Kafka, S3)
SessionProvider: creates request-scoped AsyncSession
"""
from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.kafka_streams.producer import KafkaProducerWrapper
from backend.shared.settings.config import Settings
from backend.storage.pg.database import Database
from backend.storage.redis.client import RedisClient
from backend.storage.s3.client import S3Client


class AppProvider(Provider):
    """
    Singleton infrastructure objects (scope=APP).
    Instances are created once at app start from the context passed to
    make_async_container().
    """
    scope = Scope.APP

    @provide
    def settings(self, settings: Settings) -> Settings:  # type: ignore[override]
        return settings

    @provide
    def database(self, db: Database) -> Database:  # type: ignore[override]
        return db

    @provide
    def redis_client(self, redis: RedisClient) -> RedisClient:  # type: ignore[override]
        return redis

    @provide
    def kafka_producer(self, producer: KafkaProducerWrapper) -> KafkaProducerWrapper:  # type: ignore[override]
        return producer

    @provide
    def s3_client(self, s3: S3Client | None) -> S3Client | None:  # type: ignore[override]
        return s3


class SessionProvider(Provider):
    """
    Per-request AsyncSession (scope=REQUEST).
    Session is closed after every HTTP request.
    """
    scope = Scope.REQUEST

    @provide
    async def session(self, db: Database) -> AsyncIterator[AsyncSession]:
        session = db.session()
        try:
            yield session
        finally:
            await session.close()
