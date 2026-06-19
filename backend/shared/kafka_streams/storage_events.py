"""
S3 event payloads and publish helpers.

Flow for any external write/delete operation:
  1. API receives request
  2. UseCase writes metadata to DB, sets status=PENDING
  3. UseCase calls publish_s3_upload() / publish_s3_delete()
  4. Kafka consumer picks up the event, performs the actual S3 call
  5. Consumer updates status -> DONE or FAILED (with retry)
"""
import base64

from pydantic import BaseModel

from backend.shared.kafka_streams.producer import KafkaProducerWrapper


class S3UploadEvent(BaseModel):
    key: str
    content_base64: str
    content_type: str
    metadata: dict[str, str] = {}
    original_filename: str | None = None


class S3DeleteEvent(BaseModel):
    key: str
    metadata: dict[str, str] = {}


async def publish_s3_upload(
    producer: KafkaProducerWrapper,
    topic: str,
    *,
    key: str,
    body: bytes,
    content_type: str,
    metadata: dict[str, str] | None = None,
    original_filename: str | None = None,
) -> None:
    event = S3UploadEvent(
        key=key,
        content_base64=base64.b64encode(body).decode("ascii"),
        content_type=content_type,
        metadata=metadata or {},
        original_filename=original_filename,
    )
    await producer.send(topic, event.model_dump())


async def publish_s3_delete(
    producer: KafkaProducerWrapper,
    topic: str,
    *,
    key: str,
    metadata: dict[str, str] | None = None,
) -> None:
    event = S3DeleteEvent(key=key, metadata=metadata or {})
    await producer.send(topic, event.model_dump())
