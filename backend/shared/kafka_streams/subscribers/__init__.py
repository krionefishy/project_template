from backend.shared.kafka_streams.subscribers.s3 import (
    run_example_delete_consumer,
    run_example_upload_consumer,
)

s3_consumers: list = [
    run_example_upload_consumer,
    run_example_delete_consumer,
]

__all__ = [
    "s3_consumers",
    "run_example_upload_consumer",
    "run_example_delete_consumer",
]
