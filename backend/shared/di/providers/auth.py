from dishka import Provider, Scope, provide
from fastapi import Request

from backend.app.auth.deps import AuthContext, build_auth_context
from backend.app.auth.services import PasswordService, RefreshTokenStore, RsaKeyProvider
from backend.app.auth.usecases.login_usecase import LoginUseCase
from backend.app.auth.usecases.refresh_token_usecase import RefreshTokenUseCase
from backend.shared.config import Settings
from backend.storage.redis.client import RedisClient


class AuthProvider(Provider):
    """APP-scoped auth services — created once at startup."""
    rsa_keys = provide(RsaKeyProvider, scope=Scope.APP)
    password_service = provide(PasswordService, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def refresh_token_store(self, redis: RedisClient, settings: Settings) -> RefreshTokenStore:
        return RefreshTokenStore(redis=redis, settings=settings)


class AuthContextProvider(Provider):
    """Per-request AuthContext — parsed from Bearer token via build_auth_context()."""
    scope = Scope.REQUEST

    @provide
    async def auth_context(
        self,
        request: Request,
        settings: Settings,
    ) -> AuthContext:
        return await build_auth_context(request, settings)


class AuthUsecaseProvider(Provider):
    scope = Scope.REQUEST

    login = provide(LoginUseCase)
    refresh_token = provide(RefreshTokenUseCase)
