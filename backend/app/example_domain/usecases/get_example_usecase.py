import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.deps import AuthContext
from backend.app.example_domain.db_models import ExampleModel
from backend.app.example_domain.exceptions import ExampleNotFoundError
from backend.app.example_domain.schemas.dto import ExampleDTO
from backend.storage.s3.client import S3Client

logger = logging.getLogger(__name__)


class GetExampleUseCase:
    def __init__(self, session: AsyncSession, s3_client: S3Client | None) -> None:
        self.session = session
        self.s3_client = s3_client

    async def execute(self, example_id: uuid.UUID, ctx: AuthContext) -> ExampleDTO:
        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.id == example_id)
        )
        example = result.scalar_one_or_none()
        if example is None:
            logger.warning("Example not found: id=%s", example_id)
            raise ExampleNotFoundError(f"Example {example_id} not found")

        dto = ExampleDTO.model_validate(example)

        if self.s3_client:
            for file_dto in dto.files:
                if file_dto.status.value == "done":
                    file_dto.download_url = self.s3_client.generate_presigned_url(file_dto.s3_file_key)
        else:
            logger.debug("S3 client not configured — presigned URLs unavailable")

        return dto
