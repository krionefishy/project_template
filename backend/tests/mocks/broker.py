from __future__ import annotations

import json
from typing import Any

from backend.shared.kafka_streams.producer import KafkaProducerWrapper


class FakeKafkaBroker(KafkaProducerWrapper):
    """
    In-memory Kafka producer for tests.

    Captures all sent messages — no real Kafka connection.
    Provides rich assertion helpers: get_messages_for_topic(), was_message_published().

    Usage in tests:
        # Access via conftest fixture (already injected into DI container)
        messages = fake_kafka.get_messages_for_topic("storage.s3.example.upload")
        assert len(messages) == 1
        assert messages[0]["key"].startswith("examples/")

        # Or check by predicate
        assert fake_kafka.was_message_published(
            "storage.s3.example.upload",
            predicate=lambda m: m.get("content_type") == "application/pdf",
        )
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Skip KafkaProducerWrapper.__init__ — no real producer needed
        self._producer = None
        self.published: list[tuple[str, Any]] = []

    async def send(self, topic: str, payload: dict[str, Any], key: str | None = None) -> None:
        self.published.append((topic, payload))

    async def stop(self) -> None:
        pass

    # --- Assertion helpers ---

    def get_messages_for_topic(self, topic: str) -> list[Any]:
        """Return all message payloads published to *topic*."""
        return [msg for t, msg in self.published if t == topic]

    def was_message_published(
        self,
        topic: str,
        predicate: Any = None,
    ) -> bool:
        """
        Return True if at least one message was published to *topic*.
        Optionally filter by *predicate(payload) → bool*.
        """
        messages = self.get_messages_for_topic(topic)
        if predicate is None:
            return len(messages) > 0
        return any(predicate(msg) for msg in messages)

    def clear_published(self) -> None:
        self.published.clear()

    @property
    def published_topics(self) -> list[str]:
        """Unique topics that received at least one message."""
        return list(dict.fromkeys(t for t, _ in self.published))
