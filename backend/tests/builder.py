"""
Test data Builder.

Rules:
- All entities created via SQLAlchemy insert().values().returning()
- Private __fields for lazy singleton defaults (check `is None`, then build)
- frozen_datetime injected for deterministic timestamps
- flush() after each insert (not commit — commit is the outer transaction's job)

Usage:
    async def test_something(builder: Builder):
        example = await builder.build_example(title="My Example")
        default = await builder.default_example          # same instance per test
        file = await builder.build_example_file(example_id=example.id)
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.example_domain.db_models import (
    ExampleFileModel,
    ExampleModel,
    ExampleStatus,
    FileStatus,
)


class Builder:
    def __init__(self, session: AsyncSession, default_datetime: datetime) -> None:
        self._session = session
        self._default_datetime = default_datetime

        # Lazy singletons — created once per test on first access
        self.__example: ExampleModel | None = None

    # --- Default entities (lazy, cached per test) ---

    @property
    async def default_example(self) -> ExampleModel:
        if self.__example is None:
            self.__example = await self.build_example(title="Default Example")
        return self.__example

    # --- Build methods ---

    async def build_example(
        self,
        *,
        title: str = "Test Example",
        description: str | None = None,
        status: ExampleStatus = ExampleStatus.ACTIVE,
    ) -> ExampleModel:
        result = await self._session.execute(
            insert(ExampleModel)
            .values(
                id=uuid.uuid4(),
                title=title,
                description=description,
                status=status.value,
            )
            .returning(ExampleModel)
        )
        example = result.scalar_one()
        await self._session.flush()
        return example

    async def build_example_file(
        self,
        *,
        example_id: uuid.UUID,
        s3_file_key: str | None = None,
        original_filename: str = "test.pdf",
        content_type: str = "application/pdf",
        status: FileStatus = FileStatus.DONE,
    ) -> ExampleFileModel:
        key = s3_file_key or f"examples/{example_id}/{uuid.uuid4()}/test.pdf"
        result = await self._session.execute(
            insert(ExampleFileModel)
            .values(
                id=uuid.uuid4(),
                example_id=example_id,
                s3_file_key=key,
                original_filename=original_filename,
                content_type=content_type,
                status=status.value,
            )
            .returning(ExampleFileModel)
        )
        file = result.scalar_one()
        await self._session.flush()
        return file

    # --- Add build_<domain> methods for each new domain below ---
    # async def build_user(self, *, role: str = "user", ...) -> UserModel: ...
