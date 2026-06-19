# Redis Storage

## Использование

Redis используется для:
- **Refresh токены** — хранение с TTL (`RefreshTokenStore`)
- **Кэширование** — часто запрашиваемые данные
- **Rate limiting** — ограничение запросов
- **Distributed locks** — если нужна синхронизация между воркерами

## НЕ используется для

- Очереди задач (для этого — Kafka)
- Основного хранения данных (для этого — PostgreSQL)

## Пример использования

```python
class MyService:
    def __init__(self, redis: RedisClient) -> None:
        self.redis = redis

    async def cache_result(self, key: str, value: str, ttl: int = 300) -> None:
        await self.redis.set(f"cache:{key}", value, ex=ttl)

    async def get_cached(self, key: str) -> str | None:
        return await self.redis.get(f"cache:{key}")
```

## Конфигурация

```yaml
redis:
  host: "localhost"  # Docker: redis
  port: 6379
  password: null     # Установить в production
  db: 0
```
