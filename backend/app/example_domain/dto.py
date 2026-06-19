"""
Output (response) Pydantic models for example_domain.

Rules:
- All API response shapes live here
- Use model_config = ConfigDict(from_attributes=True) for ORM → DTO mapping
- Never expose raw DB model attributes directly in API responses
- Nullable presigned URLs indicate file upload is still pending
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.example_domain.db_models import ExampleStatus, FileStatus


class ExampleFileDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    s3_file_key: str
    original_filename: str | None
    content_type: str
    status: FileStatus
    created_at: datetime
    # Presigned URL is generated on demand — not stored in DB
    download_url: str | None = None


class ExampleDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: ExampleStatus
    created_at: datetime
    updated_at: datetime
    files: list[ExampleFileDTO] = []


class ExampleListDTO(BaseModel):
    items: list[ExampleDTO]
    total: int
