import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import AliasChoices, BaseModel, Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class DatabaseConfig(BaseModel):
    url: str = "postgresql+asyncpg://user:password@localhost:5432/app_db"
    echo: bool = False


class RedisConfig(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    db: int = 0


class KafkaConfig(BaseModel):
    bootstrap_servers: str = "localhost:9092"
    consumer_group: str = "app-group"
    max_request_size: int = 10_485_760


class S3Config(BaseModel):
    endpoint_url: str = "http://localhost:9000"
    key_id: str = ""
    secret_key: str = ""
    bucket_name: str = "app-bucket"
    region: str = "ru-central-1"
    tenant_id: str = ""
    verify: bool = True

    def resolved_access_key(self) -> str:
        if self.tenant_id:
            return f"{self.tenant_id}:{self.key_id}"
        return self.key_id


class JWTConfig(BaseModel):
    secret_key: str = Field(
        default="change-me-in-production",
        validation_alias=AliasChoices("secret_key", "secret"),
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(
        default=15,
        validation_alias=AliasChoices("access_token_expire_minutes", "access_expire_seconds"),
    )
    refresh_token_expire_days: int = Field(
        default=30,
        validation_alias=AliasChoices("refresh_token_expire_days", "refresh_expire_seconds"),
    )
    rsa_private_key_pem: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalise_legacy_expirations(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalised = dict(data)
        if (
            "access_token_expire_minutes" not in normalised
            and "access_expire_seconds" in normalised
        ):
            normalised["access_token_expire_minutes"] = max(
                1,
                int(normalised["access_expire_seconds"]) // 60,
            )
        if (
            "refresh_token_expire_days" not in normalised
            and "refresh_expire_seconds" in normalised
        ):
            normalised["refresh_token_expire_days"] = max(
                1,
                int(normalised["refresh_expire_seconds"]) // (24 * 60 * 60),
            )
        return normalised

    @property
    def refresh_expire_seconds(self) -> int:
        return self.refresh_token_expire_days * 24 * 60 * 60


class RSAConfig(BaseModel):
    enabled: bool = True
    private_key_path: str = "keys/private.pem"


class AppConfig(BaseModel):
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    log_level: str = "INFO"
    service_name: str = "app"
    docs_enabled: bool = True


def settings_dir() -> Path:
    return Path(__file__).resolve().parent / "settings"


def default_config_path() -> Path:
    config_path = settings_dir() / "config.yaml"
    if config_path.exists():
        return config_path
    return settings_dir() / "config.yaml.example"


def _expand_env_vars(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _expand_env_vars(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(item) for item in value]
    if isinstance(value, str):
        return os.path.expandvars(value)
    return value


def _resolve_config_path() -> Path:
    raw_path = os.environ.get("CONFIG_PATH")
    if raw_path:
        return Path(raw_path)
    return default_config_path()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app: AppConfig = AppConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    kafka: KafkaConfig = KafkaConfig()
    s3: S3Config = S3Config()
    jwt: JWTConfig = JWTConfig()
    rsa: RSAConfig = RSAConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_source = YamlConfigSettingsSource(settings_cls, yaml_file=_resolve_config_path())
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_source,
            file_secret_settings,
        )


def load_settings(config_path: Path | str | None = None) -> Settings:
    previous_config_path = os.environ.get("CONFIG_PATH")
    try:
        if config_path is not None:
            os.environ["CONFIG_PATH"] = str(config_path)

        path = _resolve_config_path()
        if not path.exists():
            raise FileNotFoundError(f"Settings file not found: {path}")

        raw = yaml.safe_load(path.read_text()) or {}
        expanded = _expand_env_vars(raw)
        settings = Settings(**expanded)

        if db_url := os.environ.get("DATABASE_URL"):
            settings.database.url = db_url
        if kafka_servers := os.environ.get("KAFKA_BOOTSTRAP_SERVERS"):
            settings.kafka.bootstrap_servers = kafka_servers
        if jwt_secret := os.environ.get("JWT_SECRET"):
            settings.jwt.secret_key = jwt_secret

        return settings
    finally:
        if previous_config_path is None:
            os.environ.pop("CONFIG_PATH", None)
        else:
            os.environ["CONFIG_PATH"] = previous_config_path
