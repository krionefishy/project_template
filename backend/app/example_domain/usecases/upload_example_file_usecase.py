import logging
import uuid

from fastapi import HTTPException
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.auth.deps import AuthContext
from backend.app.example_domain.db_models import ExampleFileModel, ExampleModel, FileStatus
from backend.app.example_domain.dto import ExampleFileDTO
from backend.app.example_domain.exceptions import ExampleFileUploadError, ExampleNotFoundError
from backend.shared.kafka_streams.producer import KafkaProducerWrapper
from backend.shared.kafka_streams.storage_events import publish_s3_upload
from backend.shared.kafka_streams.topics import StorageTopics

logger = logging.getLogger(__name__)


class UploadExampleFileUseCase:
    ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png", "application/pdf"})
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 MB

    def __init__(self, session: AsyncSession, kafka_producer: KafkaProducerWrapper) -> None:
        self.session = session
        self.kafka_producer = kafka_producer

    async def execute(
        self,
        example_id: uuid.UUID,
        filename: str,
        content_type: str,
        payload: bytes,
        ctx: AuthContext,
    ) -> ExampleFileDTO:
        if content_type not in self.ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=415, detail=f"Unsupported content type: {content_type}")
        if len(payload) > self.MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")

        result = await self.session.execute(
            select(ExampleModel).where(ExampleModel.id == example_id)
        )
        if result.scalar_one_or_none() is None:
            logger.warning("Example not found for file upload: id=%s", example_id)
            raise ExampleNotFoundError(f"Example {example_id} not found")

        s3_key = ExampleFileModel.generate_s3_key(example_id, filename)
        file_id = uuid.uuid4()

        result = await self.session.execute(
            insert(ExampleFileModel)
            .values(
                id=file_id,
                example_id=example_id,
                s3_file_key=s3_key,
                original_filename=filename,
                content_type=content_type,
                status=FileStatus.PENDING,
            )
            .returning(ExampleFileModel)
        )
        file_record = result.scalar_one()
        await self.session.commit()

        try:
            await publish_s3_upload(
                self.kafka_producer,
                StorageTopics.EXAMPLE_UPLOAD,
                key=s3_key,
                body=payload,
                content_type=content_type,
                metadata={"example_id": str(example_id), "file_id": str(file_id)},
                original_filename=filename,
            )
        except Exception as exc:
            logger.error("Failed to publish S3 upload event for file_id=%s: %s", file_id, exc)
            raise ExampleFileUploadError("Failed to queue file for upload") from exc

        return ExampleFileDTO.model_validate(file_record)
