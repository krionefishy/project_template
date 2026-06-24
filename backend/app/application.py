import logging
import os
from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.router import api_router
from backend.shared.config import Settings, default_config_path, load_settings
from backend.shared.di.providers.provider import ALL_PROVIDERS
from backend.shared.exceptions import AppError
from backend.shared.kafka_streams.kafka import start_kafka, stop_kafka
from backend.shared.kafka_streams.producer import KafkaProducerWrapper
from backend.shared.kafka_streams.subscribers import s3_consumers
from backend.storage.pg.database import Database
from backend.storage.redis.client import RedisClient
from backend.storage.s3.client import S3Client


class Application:

    def __init__(self):
        config_path = os.getenv("CONFIG_PATH", str(default_config_path()))
        self.settings: Settings = load_settings(config_path)
        self.app: FastAPI = FastAPI(
            title=self.settings.app.service_name,
            version="1.0.0",
            lifespan=self.lifespan,
            docs_url="/api/docs" if self.settings.app.docs_enabled else None,
            redoc_url="/api/redoc" if self.settings.app.docs_enabled else None,
            openapi_url="/api/openapi.json" if self.settings.app.docs_enabled else None,
        )
        self.db: Database = Database()
        self.redis_client = RedisClient(
            host=self.settings.redis.host,
            port=self.settings.redis.port,
            password=self.settings.redis.password,
            db=self.settings.redis.db,
        )
        self.s3_client: S3Client | None = None
        self.kafka_producer = KafkaProducerWrapper(None)

        self._setup_logging()
        self._init_s3_client()

        container = make_async_container(
            *ALL_PROVIDERS,
            context={
                Settings: self.settings,
                Database: self.db,
                RedisClient: self.redis_client,
                KafkaProducerWrapper: self.kafka_producer,
                S3Client | None: self.s3_client,
            },
        )
        self.container = container
        setup_dishka(container, self.app)

        self._setup_routes()
        self._setup_middleware()
        self._setup_exception_handlers()

    def _setup_middleware(self):
        cors_origins = self._get_cors_origins()
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _get_cors_origins(self) -> list[str]:
        raw = os.getenv("CORS_ORIGINS", "*").strip()
        if not raw or raw == "*":
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    def _setup_routes(self):
        self.app.include_router(api_router, prefix="/api/v1")

    def _setup_exception_handlers(self):
        @self.app.exception_handler(AppError)
        async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
            )

    def _init_s3_client(self) -> None:
        cfg = self.settings.s3
        if not cfg.key_id or not cfg.endpoint_url:
            logging.getLogger("main").info("S3 not configured — file uploads disabled")
            return
        try:
            self.s3_client = S3Client(
                endpoint_url=self.settings.s3.endpoint_url,
                access_key=self.settings.s3.resolved_access_key(),
                secret_key=self.settings.s3.secret_key,
                bucket=self.settings.s3.bucket_name,
                region=self.settings.s3.region,
                verify=self.settings.s3.verify,
            )
        except Exception as e:
            logging.getLogger("main").warning("S3 not available: %s", e)

    async def _on_startup(self):
        logger = logging.getLogger("main")
        logger.info("App starting...")

        await self.db.connect(
            db_url=self.settings.database.url,
            echo=self.settings.database.echo,
        )
        logger.info("Database connected")

        await self.redis_client.connect()
        logger.info("Redis connected")

        if self.s3_client is not None:
            logger.info("S3 client initialized")

        try:
            await start_kafka(
                app=self.app,
                bootstrap_servers=self.settings.kafka.bootstrap_servers,
                consumer_group=self.settings.kafka.consumer_group,
                s3_client=self.s3_client,
                consumers=s3_consumers,
                kafka_producer=self.kafka_producer,
            )
            logger.info("Kafka started")
        except Exception as exc:
            logger.warning("Kafka unavailable, continuing without it: %s", exc)

        logger.info("App started successfully")

    async def _on_shutdown(self):
        logger = logging.getLogger("main")
        logger.info("App shutting down...")

        await stop_kafka(self.app)

        await self.container.close()

        if self.redis_client:
            await self.redis_client.disconnect()

        await self.db.disconnect()
        logger.info("App stopped")

    async def _safe_on_shutdown(self) -> None:
        try:
            await self._on_shutdown()
        except Exception:
            logging.getLogger("main").exception("App shutdown failed")

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        try:
            await self._on_startup()
        except Exception:
            logging.getLogger("main").exception("App startup failed")
            await self._safe_on_shutdown()
            raise

        try:
            yield
        finally:
            await self._safe_on_shutdown()

    def _setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.settings.app.log_level.upper(), logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def get_app(self) -> FastAPI:
        return self.app


def create_app() -> FastAPI:
    application = Application()
    return application.get_app()
