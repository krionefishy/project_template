import uuid
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, File, UploadFile

from backend.app.auth.deps import AuthContext, require_auth
from backend.app.example_domain.schemas.domain import CreateExampleRequest
from backend.app.example_domain.schemas.dto import ExampleDTO, ExampleFileDTO
from backend.app.example_domain.usecases.create_example_usecase import CreateExampleUseCase
from backend.app.example_domain.usecases.get_example_usecase import GetExampleUseCase
from backend.app.example_domain.usecases.upload_example_file_usecase import UploadExampleFileUseCase

router = APIRouter(
    prefix="/examples",
    tags=["examples"],
    route_class=DishkaRoute,
)


@router.get("/{example_id}", response_model=ExampleDTO)
async def get_example(
    example_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_auth)],
    usecase: FromDishka[GetExampleUseCase],
) -> ExampleDTO:
    return await usecase.execute(example_id, auth)


@router.post("/", response_model=ExampleDTO, status_code=201)
async def create_example(
    request: CreateExampleRequest,
    auth: Annotated[AuthContext, Depends(require_auth)],
    usecase: FromDishka[CreateExampleUseCase],
) -> ExampleDTO:
    return await usecase.execute(request, auth)


@router.post("/{example_id}/files", response_model=ExampleFileDTO, status_code=200)
async def upload_example_file(
    example_id: uuid.UUID,
    auth: Annotated[AuthContext, Depends(require_auth)],
    usecase: FromDishka[UploadExampleFileUseCase],
    file: UploadFile = File(...),
) -> ExampleFileDTO:
    """
    Upload a file. Returns 200 with status=PENDING.
    File is queued for S3 upload via Kafka — poll GET /{example_id} for status.
    """
    payload = await file.read()
    return await usecase.execute(
        example_id=example_id,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        payload=payload,
        ctx=auth,
    )
