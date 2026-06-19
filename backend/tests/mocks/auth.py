"""
Auth mocks for tests — no bcrypt hashing, no Redis, no RSA decryption.
"""
from typing import Any
from uuid import UUID


class MockPasswordService:
    """
    Password service mock that stores plain-text passwords.
    hash("secret") → "hashed_secret"
    verify("secret", "hashed_secret") → True
    """

    def __init__(self) -> None:
        self._hashes: dict[str, str] = {}
        self._calls: list[dict[str, Any]] = []

    def hash(self, password: str) -> str:
        self._calls.append({"method": "hash", "password": password})
        hashed = f"hashed_{password}"
        self._hashes[hashed] = password
        return hashed

    def verify(self, password: str, hashed: str) -> bool:
        self._calls.append({"method": "verify", "password": password, "hashed": hashed})
        return self._hashes.get(hashed) == password

    def decrypt(self, encrypted: bytes) -> bytes:
        """Mock RSA decrypt — returns input unchanged."""
        self._calls.append({"method": "decrypt"})
        return encrypted if isinstance(encrypted, bytes) else encrypted.encode()


class MockRefreshTokenStore:
    """In-memory refresh token store — no Redis required."""

    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    async def save(self, user_id: UUID, token: str) -> None:
        self._tokens[token] = str(user_id)

    async def get_user_id(self, token: str) -> UUID | None:
        value = self._tokens.get(token)
        return UUID(value) if value else None

    async def revoke(self, token: str) -> None:
        self._tokens.pop(token, None)

    def clear(self) -> None:
        self._tokens.clear()
