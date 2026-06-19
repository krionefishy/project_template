"""
Kafka topic names.

Naming convention: <domain>.<entity>.<action>
  - domain:  storage, notification, billing, ...
  - entity:  s3, email, invoice, ...
  - action:  upload, delete, send, process, ...

Add new topics here as project grows.
All consumers and producers must reference constants from this module.
"""


class StorageTopics:
    SERVICE = "storage"
    GROUP = "s3"

    # Replace EXAMPLE with actual entity names, e.g. AVATAR, DOCUMENT, REPORT
    EXAMPLE_UPLOAD = f"{SERVICE}.{GROUP}.example.upload"
    EXAMPLE_DELETE = f"{SERVICE}.{GROUP}.example.delete"

    @classmethod
    def all_s3_mutation_topics(cls) -> list[str]:
        return [
            cls.EXAMPLE_UPLOAD,
            cls.EXAMPLE_DELETE,
        ]
