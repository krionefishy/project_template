from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    async def connect(self, db_url: str, *, echo: bool = False) -> None:
        self._engine = create_async_engine(
            url=db_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autobegin=True,
        )

    async def disconnect(self) -> None:
        if self._engine:
            await self._engine.dispose()

    def session(self) -> AsyncSession:
        assert self._session_factory is not None, "Database is not connected"
        return self._session_factory()
