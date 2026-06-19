"""
RefreshTokenUseCase — exchange valid refresh token for a new access token.
"""
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import jwt

from backend.app.auth.domain import RefreshRequest
from backend.app.auth.dto import TokenPairDTO
from backend.app.auth.services import RefreshTokenStore
from backend.shared.settings.config import Settings


class RefreshTokenUseCase:
    def __init__(self, settings: Settings, refresh_token_store: RefreshTokenStore) -> None:
        self.settings = settings
        self.refresh_tokens = refresh_token_store

    async def execute(self, request: RefreshRequest) -> TokenPairDTO:
        user_id = await self.refresh_tokens.get_user_id(request.refresh_token)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token invalid or expired",
            )

        # Rotate refresh token
        await self.refresh_tokens.revoke(request.refresh_token)
        new_refresh = str(uuid.uuid4())
        await self.refresh_tokens.save(user_id, new_refresh)

        # Issue new access token
        # TODO: fetch actual user role from DB
        role = "user"
        access_token = self._make_access_token(user_id, role)

        return TokenPairDTO(access_token=access_token, refresh_token=new_refresh)

    def _make_access_token(self, user_id: uuid.UUID, role: str) -> str:
        cfg = self.settings.jwt
        expire = datetime.now(UTC) + timedelta(minutes=cfg.access_token_expire_minutes)
        payload = {"sub": str(user_id), "role": role, "exp": expire}
        return jwt.encode(payload, cfg.secret_key, algorithm=cfg.algorithm)
