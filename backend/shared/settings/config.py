import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Config dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DatabaseConfig:
    url: str = "postgresql+asyncpg://user:password@localhost:5432/app_db"
    echo: bool = False


@dataclass
class RedisConfig:
    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    db: int = 0


@dataclass
class KafkaConfig:
    bootstrap_servers: str = "localhost:9092"
    consumer_group: str = "app-group"


@dataclass
class S3Config:
    endpoint_url: str = "http://localhost:9000"
    # Yandex Cloud / Cloud.ru: key_id only (tenant_id prepended separately)
    key_id: str = ""
    secret_key: str = ""
    bucket_name: str = "app-bucket"
    region: str = "ru-central-1"
    tenant_id: str = ""
    verify: bool = True  # Set False for self-signed certs (MinIO, dev)

    def resolved_access_key(self) -> str:
        """Build access key: tenant_id:key_id for Yandex/Cloud.ru, plain key_id otherwise."""
        if self.tenant_id:
            return f"{self.tenant_id}:{self.key_id}"
        return self.key_id


@dataclass
class JWTConfig:
    secret: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_expire_seconds: int = 900        # 15 min
    refresh_expire_seconds: int = 2_592_000  # 30 days
    rsa_private_key_pem: str | None = None  # PEM string; if None — ephemeral key generated


@dataclass
class RSAConfig:
    """RSA key pair for frontend password encryption. Set enabled=false if not needed."""
    enabled: bool = True
    private_key_path: str = "keys/private.pem"


@dataclass
class AppConfig:
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    log_level: str = "INFO"
    # Change to your service name
    service_name: str = "app"


@dataclass
class Settings:
    app: AppConfig = field(default_factory=AppConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    s3: S3Config = field(default_factory=S3Config)
    jwt: JWTConfig = field(default_factory=JWTConfig)
    rsa: RSAConfig = field(default_factory=RSAConfig)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _merge_dict(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def _from_dict(cls: type, data: dict):
    """Recursively build dataclass from dict."""
    import dataclasses

    if not dataclasses.is_dataclass(cls):
        return data
    kwargs = {}
    for f in dataclasses.fields(cls):
        if f.name in data:
            val = data[f.name]
            if dataclasses.is_dataclass(f.type) and isinstance(val, dict):
                kwargs[f.name] = _from_dict(f.type, val)
            else:
                kwargs[f.name] = val
    return cls(**kwargs)


def settings_dir() -> Path:
    return Path(__file__).resolve().parent


def default_config_path() -> Path:
    return settings_dir() / "config.yaml"


def load_settings(config_path: Path | str | None = None) -> Settings:
    path = Path(config_path) if config_path else _default_config_path()

    with open(path) as f:
        raw: dict = yaml.safe_load(f) or {}

    settings = Settings()

    # Apply YAML values
    if "app" in raw:
        settings.app = _from_dict(AppConfig, raw["app"])
    if "database" in raw:
        settings.database = _from_dict(DatabaseConfig, raw["database"])
    if "redis" in raw:
        settings.redis = _from_dict(RedisConfig, raw["redis"])
    if "kafka" in raw:
        settings.kafka = _from_dict(KafkaConfig, raw["kafka"])
    if "s3" in raw:
        settings.s3 = _from_dict(S3Config, raw["s3"])
    if "jwt" in raw:
        settings.jwt = _from_dict(JWTConfig, raw["jwt"])
    if "rsa" in raw:
        settings.rsa = _from_dict(RSAConfig, raw["rsa"])

    # Allow env overrides for secrets / CI
    if db_url := os.environ.get("DATABASE_URL"):
        settings.database.url = db_url
    if kafka_servers := os.environ.get("KAFKA_BOOTSTRAP_SERVERS"):
        settings.kafka.bootstrap_servers = kafka_servers
    if jwt_secret := os.environ.get("JWT_SECRET"):
        settings.jwt.secret = jwt_secret

    return settings
