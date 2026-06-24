from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from backend.app.auth.schemas.domain import LoginRequest, RefreshRequest
from backend.app.auth.schemas.dto import PublicKeyDTO, TokenPairDTO
from backend.app.auth.services import RsaKeyProvider
from backend.app.auth.usecases.login_usecase import LoginUseCase
from backend.app.auth.usecases.refresh_token_usecase import RefreshTokenUseCase

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    route_class=DishkaRoute,
)


@router.get("/public-key", response_model=PublicKeyDTO)
async def get_public_key(rsa: FromDishka[RsaKeyProvider]) -> PublicKeyDTO:
    """Return RSA public key for frontend password encryption."""
    return PublicKeyDTO(public_key=rsa.get_public_key_pem())


@router.post("/login", response_model=TokenPairDTO)
async def login(
    request: LoginRequest,
    usecase: FromDishka[LoginUseCase],
) -> TokenPairDTO:
    return await usecase.execute(request)


@router.post("/refresh", response_model=TokenPairDTO)
async def refresh(
    request: RefreshRequest,
    usecase: FromDishka[RefreshTokenUseCase],
) -> TokenPairDTO:
    return await usecase.execute(request)
