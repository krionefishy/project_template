import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.app.example_domain.db_models import ExampleStatus, FileStatus


class ExampleFileDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    s3_file_key: str
    original_filename: str | None
    content_type: str
    status: FileStatus
    created_at: datetime
    download_url: str | None = None


class ExampleDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None
    status: ExampleStatus
    created_at: datetime
    updated_at: datetime
    files: list[ExampleFileDTO] = Field(default_factory=list)


class ExampleListDTO(BaseModel):
    items: list[ExampleDTO]
    total: int
