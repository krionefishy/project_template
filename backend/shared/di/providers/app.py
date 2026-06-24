"""
Infrastructure-level Dishka providers.

AppProvider:     creates app-scoped singletons (DB, Redis, Kafka, S3)
SessionProvider: creates request-scoped AsyncSession
"""
from collections.abc import AsyncIterator

from dishka import Provider, Scope, from_context, provide
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.config import Settings
from backend.shared.kafka_streams.producer import KafkaProducerWrapper
from backend.storage.pg.database import Database
from backend.storage.redis.client import RedisClient
from backend.storage.s3.client import S3Client


class AppProvider(Provider):
    scope = Scope.APP

    settings = from_context(Settings)
    database = from_context(Database)
    redis_client = from_context(RedisClient)
    kafka_producer = from_context(KafkaProducerWrapper)
    s3_client = from_context(S3Client | None)


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
