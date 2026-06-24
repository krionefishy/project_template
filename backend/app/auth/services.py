"""
Auth infrastructure services.

RsaKeyProvider:     lazy RSA key pair — loads from PEM file or generates ephemeral
PasswordService:    bcrypt hashing + RSA decryption of frontend-encrypted passwords
RefreshTokenStore:  Redis-backed refresh token storage with TTL
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from threading import Lock

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from passlib.context import CryptContext

from backend.shared.config import Settings
from backend.storage.redis.client import RedisClient

logger = logging.getLogger("auth")
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RsaKeyProvider:
    """
    Loads RSA private key once (lazy, thread-safe).

    Key source priority:
    1. settings.rsa.private_key_path — PEM file on disk
    2. Ephemeral key — generated at startup (tokens break on restart; dev only)
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._private_key: RSAPrivateKey | None = None
        self._public_key_pem: str | None = None
        self._lock = Lock()

    def _ensure_loaded(self) -> None:
        if self._private_key is not None:
            return
        with self._lock:
            if self._private_key is not None:
                return
            pem_string = self._settings.jwt.rsa_private_key_pem
            if pem_string:
                loaded_key = serialization.load_pem_private_key(pem_string.encode(), password=None)
                if not isinstance(loaded_key, RSAPrivateKey):
                    raise TypeError("RSA private key PEM is required")
                self._private_key = loaded_key
                logger.info("RSA private key loaded from config (PEM string)")
            else:
                key_path = Path(self._settings.rsa.private_key_path)
                if key_path.exists():
                    loaded_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
                    if not isinstance(loaded_key, RSAPrivateKey):
                        raise TypeError(f"RSA private key expected in {key_path}")
                    self._private_key = loaded_key
                    logger.info("RSA private key loaded from %s", key_path)
                else:
                    logger.warning(
                        "RSA private key not found at %s — generating ephemeral key. "
                        "Tokens will break on restart.",
                        key_path,
                    )
                    self._private_key = rsa.generate_private_key(
                        public_exponent=65537, key_size=2048
                    )
            assert self._private_key is not None
            pub: RSAPublicKey = self._private_key.public_key()
            self._public_key_pem = pub.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode()

    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypt password that frontend encrypted with RSA public key (OAEP/SHA-256)."""
        self._ensure_loaded()
        assert self._private_key is not None
        return self._private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def get_public_key_pem(self) -> str:
        self._ensure_loaded()
        assert self._public_key_pem is not None
        return self._public_key_pem


class PasswordService:
    def hash(self, plain: str) -> str:
        return _pwd_context.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)


class RefreshTokenStore:
    PREFIX = "refresh_token:"

    def __init__(self, redis: RedisClient, settings: Settings) -> None:
        self._redis = redis
        self._expire_seconds = settings.jwt.refresh_expire_seconds

    async def save(self, user_id: uuid.UUID, token: str) -> None:
        await self._redis.set(f"{self.PREFIX}{token}", str(user_id), expire=self._expire_seconds)

    async def get_user_id(self, token: str) -> uuid.UUID | None:
        value = await self._redis.get(f"{self.PREFIX}{token}")
        if value is None:
            return None
        return uuid.UUID(value)

    async def revoke(self, token: str) -> None:
        await self._redis.delete(f"{self.PREFIX}{token}")
