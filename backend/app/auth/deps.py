"""
FastAPI dependency functions for authentication.

AuthContext is built per-request by Dishka (AuthContextProvider).
require_auth() retrieves it from the container — no manual JWT parsing here.
Role-based deps use require_any_role() factory.

Add project-specific role functions below (see examples at bottom).
"""
from fastapi import HTTPException, Request, status
from pydantic import BaseModel

from backend.shared.settings.config import Settings


class AuthContext(BaseModel):
    user_id: str
    role: str


async def build_auth_context(
    request: Request,
    settings: Settings,
) -> AuthContext:
    """
    Parse and validate the Bearer token from the request.
    Called by Dishka AuthContextProvider on every protected request.

    Replace this implementation with your actual token validation logic:
    - Decode JWT using settings.jwt.secret_key
    - Look up user in DB via AsyncSession if needed
    - Raise HTTPException(401) on any failure
    """
    from fastapi.security.utils import get_authorization_scheme_param
    from jose import JWTError, jwt

    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)

    if not authorization or scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm],
        )
        user_id: str = payload["sub"]
        role: str = payload["role"]
    except (JWTError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return AuthContext(user_id=user_id, role=role)


async def _get_auth_context(request: Request) -> AuthContext:
    container = request.state.dishka_container
    return await container.get(AuthContext)


def require_any_role(auth: AuthContext, allowed_roles: set[str]) -> AuthContext:
    if auth.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return auth


async def require_auth(request: Request) -> AuthContext:
    return await _get_auth_context(request)


# --- Add project-specific role deps below ---
# Example:
# async def require_admin(request: Request) -> AuthContext:
#     auth = await _get_auth_context(request)
#     return require_any_role(auth, {"admin", "super_admin"})
#
# async def require_super_admin(request: Request) -> AuthContext:
#     auth = await _get_auth_context(request)
#     return require_any_role(auth, {"super_admin"})
