"""
LoginUseCase — authenticate user with RSA-encrypted password.

Flow:
1. Fetch user from DB by username
2. Decrypt password with RSA private key
3. Verify bcrypt hash
4. Issue JWT access + refresh tokens
5. Store refresh token in Redis
"""
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.domain import LoginRequest
from backend.app.auth.dto import TokenPairDTO
from backend.app.auth.services import PasswordService, RefreshTokenStore, RsaKeyProvider
from backend.shared.settings.config import Settings


class LoginUseCase:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        rsa_key_provider: RsaKeyProvider,
        password_service: PasswordService,
        refresh_token_store: RefreshTokenStore,
    ) -> None:
        self.session = session
        self.settings = settings
        self.rsa = rsa_key_provider
        self.password_service = password_service
        self.refresh_tokens = refresh_token_store

    async def execute(self, request: LoginRequest) -> TokenPairDTO:
        # 1. Find user (replace UserModel with actual ORM model)
        # result = await self.session.execute(select(UserModel).where(UserModel.username == request.username))
        # user = result.scalar_one_or_none()
        # if user is None:
        #     raise HTTPException(status_code=401, detail="Invalid credentials")

        # 2. Decrypt RSA-encrypted password sent by frontend
        try:
            plain_password = self.rsa.decrypt(request.decode_encrypted_password()).decode()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decrypt password",
            ) from exc

        # 3. Verify password
        # if not self.password_service.verify(plain_password, user.hashed_password):
        #     raise HTTPException(status_code=401, detail="Invalid credentials")

        # 4. Issue tokens (replace user_id / role with actual values)
        user_id = uuid.uuid4()  # replace with user.id
        role = "user"           # replace with user.role

        access_token = self._make_access_token(user_id, role)
        refresh_token = str(uuid.uuid4())

        # 5. Store refresh token
        await self.refresh_tokens.save(user_id, refresh_token)

        return TokenPairDTO(access_token=access_token, refresh_token=refresh_token)

    def _make_access_token(self, user_id: uuid.UUID, role: str) -> str:
        cfg = self.settings.jwt
        expire = datetime.now(UTC) + timedelta(minutes=cfg.access_token_expire_minutes)
        payload = {"sub": str(user_id), "role": role, "exp": expire}
        return jwt.encode(payload, cfg.secret_key, algorithm=cfg.algorithm)
