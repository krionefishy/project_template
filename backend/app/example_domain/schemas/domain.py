from pydantic import BaseModel, Field, field_validator

from backend.app.example_domain.db_models import ExampleStatus


class CreateExampleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=4096)
    status: ExampleStatus = ExampleStatus.ACTIVE

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        return stripped


class UpdateExampleRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: ExampleStatus | None = None
