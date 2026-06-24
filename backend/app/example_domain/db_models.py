"""
SQLAlchemy ORM models for example_domain.

Rules:
- Use Mapped[T] + mapped_column() for all columns
- All timestamps: server_default=func.now(), timezone=True
- Never inline index=True — use explicit Index() in __table_args__
- Enums defined here, imported in schemas/domain.py and schemas/dto.py
- S3 key generator: classmethod on the file model
- Properties return derived/aggregated data from relationships
- Rename 'example_domain' to your actual domain name everywhere
"""
import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.storage.pg.database import Base


class ExampleStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class FileStatus(StrEnum):
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


class ExampleModel(Base):
    __tablename__ = "examples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=ExampleStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    files: Mapped[list["ExampleFileModel"]] = relationship(
        "ExampleFileModel", back_populates="example", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_examples_status", "status"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_examples_status"),
    )

    # --- Properties — derived data from relationships ---

    @property
    def done_files(self) -> list["ExampleFileModel"]:
        """Files successfully uploaded to S3."""
        return [f for f in self.files if f.status == FileStatus.DONE]

    @property
    def pending_files(self) -> list["ExampleFileModel"]:
        """Files still queued for S3 upload."""
        return [f for f in self.files if f.status == FileStatus.PENDING]

    @property
    def has_pending_uploads(self) -> bool:
        return any(f.status == FileStatus.PENDING for f in self.files)

    @property
    def file_count(self) -> int:
        return len(self.files)


class ExampleFileModel(Base):
    __tablename__ = "example_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    example_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("examples.id", ondelete="CASCADE"),
        nullable=False,
    )
    s3_file_key: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=FileStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    example: Mapped[ExampleModel] = relationship("ExampleModel", back_populates="files")

    __table_args__ = (
        Index("ix_example_files_example_id", "example_id"),
        Index("ix_example_files_status", "status"),
        Index("ix_example_files_example_id_status", "example_id", "status"),
        CheckConstraint("status IN ('pending', 'done', 'failed')", name="ck_example_files_status"),
    )

    # --- Properties ---

    @property
    def is_ready(self) -> bool:
        """True when the file has been successfully uploaded to S3."""
        return self.status == FileStatus.DONE

    @property
    def is_image(self) -> bool:
        return self.content_type.startswith("image/")

    @classmethod
    def generate_s3_key(cls, example_id: uuid.UUID, filename: str) -> str:
        """
        Generate a unique, safe S3 object key.
        Format: examples/<example_id>/<uuid>/<safe_filename>
        """
        from backend.storage.s3.client import sanitize_key_segment
        safe_name = sanitize_key_segment(filename)
        return f"examples/{example_id}/{uuid.uuid4()}/{safe_name}"
