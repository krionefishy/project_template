import json
from typing import Any


class KafkaProducerWrapper:
    """Wrapper over AIOKafkaProducer. Send messages: await producer.send(topic, payload)."""

    def __init__(self, producer: Any = None):
        self._producer = producer

    async def send(self, topic: str, payload: dict, key: str | None = None) -> Any:
        if self._producer is None:
            return None
        value = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        encoded_key = key.encode("utf-8") if key else None
        return await self._producer.send(topic, value=value, key=encoded_key)

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
