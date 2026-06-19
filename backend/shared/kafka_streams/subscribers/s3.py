import base64
import logging

from pydantic import ValidationError

from backend.shared.kafka_streams.consumer import kafka_subscriber
from backend.shared.kafka_streams.storage_events import S3DeleteEvent, S3UploadEvent
from backend.shared.kafka_streams.topics import StorageTopics

logger = logging.getLogger(__name__)


async def _upload(s3_client, payload: dict) -> None:
    if s3_client is None:
        logger.warning("S3 upload skipped: S3 client is not configured")
        return
    try:
        event = S3UploadEvent.model_validate(payload)
    except ValidationError:
        logger.exception("Invalid S3 upload event payload")
        return
    await s3_client.put_object(
        key=event.key,
        body=base64.b64decode(event.content_base64),
        content_type=event.content_type,
        metadata=event.metadata,
    )


async def _delete(s3_client, payload: dict) -> None:
    if s3_client is None:
        logger.warning("S3 delete skipped: S3 client is not configured")
        return
    try:
        event = S3DeleteEvent.model_validate(payload)
    except ValidationError:
        logger.exception("Invalid S3 delete event payload")
        return
    await s3_client.delete_object(event.key)


@kafka_subscriber(StorageTopics.EXAMPLE_UPLOAD)
async def run_example_upload_consumer(s3_client, payload: dict) -> None:
    await _upload(s3_client, payload)


@kafka_subscriber(StorageTopics.EXAMPLE_DELETE)
async def run_example_delete_consumer(s3_client, payload: dict) -> None:
    await _delete(s3_client, payload)
