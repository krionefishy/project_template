"""
Test configuration and fixtures.

Architecture (mirrors RSD):
- Session is shared between tests and Dishka via ContextVar + TestSessionProvider
- db_session wraps each test in a transaction with join_transaction_mode="create_savepoint"
- All infra (Kafka, S3, Redis, Password) is replaced with in-memory mocks
- frozen_datetime gives tests deterministic timestamps
- builder is function-scoped, receives frozen_datetime for consistent data

Isolation:
  Each test opens one connection, begins a transaction, then uses
  join_transaction_mode="create_savepoint" so the UseCase's session.commit()
  creates a SAVEPOINT internally. The outer transaction is rolled back after
  each test, leaving the DB clean — without recreating tables.

xdist support:
  pytest_configure adjusts DATABASE_URL to db_name_<worker_id> so parallel
  workers each get their own DB.
"""
import logging
import os
import re
from collections.abc import AsyncGenerator, AsyncIterator
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from dishka import Provider, Scope, from_context, make_async_container, provide
from dishka.integrations.fastapi import FastapiProvider, setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.app.api.router import api_router
from backend.app.auth.deps import AuthContext
from backend.app.auth.services import PasswordService, RefreshTokenStore, RsaKeyProvider
from backend.shared.di.providers.auth import AuthContextProvider, AuthUsecaseProvider
from backend.shared.di.providers.example_domain import ExampleDomainProvider
from backend.shared.kafka_streams.producer import KafkaProducerWrapper
from backend.shared.settings.config import Settings, load_settings
from backend.storage.pg.database import Base, Database
from backend.storage.redis.client import RedisClient
from backend.storage.s3.client import S3Client
from backend.tests.builder import Builder
from backend.tests.mocks import FakeKafkaBroker, MockPasswordService, MockRefreshTokenStore, MockS3Client

# ---------------------------------------------------------------------------
# ContextVar — shares the current test session with Dishka's TestSessionProvider
# ---------------------------------------------------------------------------
_current_db_session: ContextVar[AsyncSession | None] = ContextVar(
    "current_test_db_session", default=None
)


# ---------------------------------------------------------------------------
# xdist: per-worker database URL (db_name_0, db_name_1, ...)
# ---------------------------------------------------------------------------

def _set_worker_database_url(config) -> None:
    if not hasattr(config, "workerinput") or not config.workerinput:
        return
    workerid = config.workerinput.get("workerid", "gw0")
    m = re.search(r"(\d+)$", workerid)
    worker_num = int(m.group(1)) if m else 0
    url = os.environ.get("DATABASE_URL")
    if not url:
        return
    parsed = urlparse(url)
    base = (parsed.path or "/").strip("/")
    if not base:
        return
    new_url = urlunparse(
        (parsed.scheme, parsed.netloc, f"/{base}_{worker_num}",
         parsed.params, parsed.query, parsed.fragment)
    )
    os.environ["DATABASE_URL"] = new_url


def pytest_configure(config):
    _set_worker_database_url(config)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def settings() -> Settings:
    config_path = os.getenv("CONFIG_PATH")
    if not config_path:
        candidates = [
            "backend/shared/settings/config.test.yaml",
            "shared/settings/config.test.yaml",
        ]
        for p in candidates:
            if Path(p).exists():
                config_path = p
                break
        config_path = config_path or "backend/shared/settings/config.test.yaml"

    cfg = load_settings(config_path)

    # Allow DATABASE_URL env override (CI, xdist)
    if db_url := os.environ.get("DATABASE_URL"):
        cfg.database.url = db_url

    return cfg


# ---------------------------------------------------------------------------
# Database engine (session-scoped — one engine for entire test run)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def db_engine(settings: Settings):
    engine = create_async_engine(
        url=settings.database.url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=False,
    )
    # Create all tables once at test session start
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
async def database(settings: Settings, db_engine) -> Database:
    db = Database()
    db._engine = db_engine
    db._session_factory = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return db


# ---------------------------------------------------------------------------
# Mocks (session-scoped singletons)
# ---------------------------------------------------------------------------

_mock_password_service = MockPasswordService()
_mock_refresh_store = MockRefreshTokenStore()


# ---------------------------------------------------------------------------
# FastAPI app with test DI container (session-scoped)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def application(database: Database, settings: Settings) -> AsyncGenerator[FastAPI]:
    """
    Build FastAPI with test-specific Dishka providers:
    - TestSessionProvider reads AsyncSession from ContextVar (set per-test)
    - FakeKafkaBroker instead of real Kafka
    - MockS3Client instead of real S3
    - MockPasswordService / MockRefreshTokenStore instead of Redis-backed ones
    """
    fake_kafka = FakeKafkaBroker()
    mock_s3 = MockS3Client()

    class TestAppProvider(Provider):
        scope = Scope.APP
        settings = from_context(Settings)
        db = from_context(Database)
        redis = from_context(RedisClient)
        kafka_producer = from_context(KafkaProducerWrapper)

        @provide
        def s3_client(self) -> S3Client:
            return mock_s3

    class TestAuthProvider(Provider):
        scope = Scope.APP

        rsa_keys = provide(RsaKeyProvider, scope=Scope.APP)

        @provide
        def password_service(self) -> PasswordService:
            return _mock_password_service

        @provide
        def refresh_token_store(self) -> RefreshTokenStore:
            return _mock_refresh_store

    class TestSessionProvider(Provider):
        """
        Per-request provider that yields the session stored in ContextVar.
        This ensures UseCase code runs inside the same transaction as the test.
        """
        scope = Scope.REQUEST

        @provide
        async def session(self) -> AsyncIterator[AsyncSession]:
            session = _current_db_session.get()
            if session is None:
                raise RuntimeError("Test DB session not set — missing db_session fixture?")
            yield session

    fastapi_app = FastAPI(title="Test App")
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fastapi_app.include_router(api_router, prefix="/api/v1")

    # Register global AppError handler (same as production)
    from backend.shared.exceptions import AppError
    from fastapi.responses import JSONResponse

    @fastapi_app.exception_handler(AppError)
    async def app_error_handler(request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    container = make_async_container(
        TestAppProvider(),
        TestSessionProvider(),
        FastapiProvider(),
        TestAuthProvider(),
        AuthContextProvider(),
        AuthUsecaseProvider(),
        # --- Add domain providers here ---
        ExampleDomainProvider(),
        context={
            Settings: settings,
            Database: database,
            RedisClient: RedisClient(host="localhost"),
            KafkaProducerWrapper: fake_kafka,
        },
    )
    setup_dishka(container, fastapi_app)

    yield fastapi_app

    await container.close()


# ---------------------------------------------------------------------------
# Per-test DB session (SAVEPOINT isolation)
# ---------------------------------------------------------------------------

@pytest.fixture
async def db_session(database: Database) -> AsyncGenerator[AsyncSession]:
    """
    Opens a connection, begins a transaction, then provides an AsyncSession with
    join_transaction_mode="create_savepoint".

    UseCase's session.commit() creates a nested SAVEPOINT — the outer transaction
    is rolled back after the test, leaving the DB clean.
    """
    async with database._engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        token = _current_db_session.set(session)
        try:
            yield session
        finally:
            _current_db_session.reset(token)
            await session.close()
            await transaction.rollback()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

@pytest.fixture
async def client(application: FastAPI, db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=application)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def frozen_datetime() -> datetime:
    """Fixed datetime for deterministic test data."""
    return datetime(2025, 1, 15, 12, 0, 0)


@pytest.fixture
def builder(db_session: AsyncSession, frozen_datetime: datetime) -> Builder:
    """
    Builder instance for creating test entities in the DB.

    Usage:
        async def test_something(builder: Builder):
            example = await builder.build_example(title="Test")
            default = await builder.default_example
    """
    return Builder(db_session, frozen_datetime)


@pytest.fixture
def bearer_headers(settings: Settings):
    """
    Factory: returns Authorization headers with a valid JWT.

    Usage:
        headers = bearer_headers(role="admin")
        headers = bearer_headers(user_id=some_uuid, role="manager")
    """
    import uuid as _uuid
    from datetime import UTC, timedelta
    from jose import jwt

    cfg = settings.jwt

    def _make(user_id=None, role: str = "user") -> dict[str, str]:
        from datetime import datetime as dt
        uid = str(user_id or _uuid.uuid4())
        expire = dt.now(UTC) + timedelta(seconds=cfg.access_expire_seconds)
        token = jwt.encode(
            {"sub": uid, "role": role, "exp": expire},
            cfg.secret,
            algorithm=cfg.algorithm,
        )
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture
def mock_password_service() -> MockPasswordService:
    return _mock_password_service


@pytest.fixture
def mock_refresh_store() -> MockRefreshTokenStore:
    return _mock_refresh_store
