"""
Input (request) Pydantic models for example_domain.

Rules:
- All request bodies live here
- Validate data here with @field_validator / @model_validator
- Do NOT put response shapes here — they belong in dto.py
- Enum types can be imported from db_models.py to stay DRY
"""
from pydantic import BaseModel, Field, field_validator

from backend.app.example_domain.db_models import ExampleStatus


class CreateExampleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)
    status: ExampleStatus = ExampleStatus.ACTIVE

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        return stripped


class UpdateExampleRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ExampleStatus | None = None
