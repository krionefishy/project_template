# UseCase слой

## Правила написания UseCase

### Структура класса

```python
class CreateOrderUseCase:
    def __init__(self, session: AsyncSession, kafka_producer: KafkaProducerWrapper) -> None:
        self.session = session
        self.kafka_producer = kafka_producer

    async def execute(self, request: CreateOrderRequest, ctx: AuthContext) -> OrderDTO | None:
        ...
```

### Обязательные правила

- **Один класс = одна операция** (`Create`, `Get`, `Update`, `Delete`, `Upload`, `List`)
- **Единственный публичный метод** — `execute()`
- **Возврат `None`** вместо 403/404 — роутер сам кидает HTTPException
- **HTTPException** только для бизнес-ошибок (409 Conflict, 415 Unsupported Media)
- **Нет слоя Repository** — работа напрямую через `AsyncSession` и SQLAlchemy query builder
- **Авторизация** в начале `execute()` — проверяй `ctx.role` перед обращением к БД

## SQLAlchemy Query Builder — всегда так, никогда не через session.add()

### SELECT

```python
result = await self.session.execute(
    select(OrderModel)
    .where(OrderModel.id == order_id)
)
order = result.scalar_one_or_none()
```

### INSERT — insert().values().returning()

```python
result = await self.session.execute(
    insert(OrderModel)
    .values(id=uuid.uuid4(), title=request.title, status=OrderStatus.NEW)
    .returning(OrderModel)
)
order = result.scalar_one()
await self.session.commit()
```

### UPDATE

```python
await self.session.execute(
    update(OrderModel)
    .where(OrderModel.id == order_id)
    .values(status=OrderStatus.DONE)
)
await self.session.commit()
```

### DELETE

```python
await self.session.execute(
    delete(OrderModel).where(OrderModel.id == order_id)
)
await self.session.commit()
```

### Что НЕЛЬЗЯ делать

```python
# ❌ ORM add/refresh — не используем
self.session.add(order)
await self.session.commit()
await self.session.refresh(order)

# ❌ Голый SQL
await self.session.execute(text("SELECT * FROM orders"))
```

## Паттерн загрузки файлов (через Kafka)

```python
# 1. SELECT: проверяем родительский объект
result = await self.session.execute(select(OrderModel).where(OrderModel.id == order_id))
if result.scalar_one_or_none() is None:
    return None

# 2. Генерируем S3 ключ
s3_key = FileModel.generate_s3_key(order_id, filename)

# 3. INSERT: статус PENDING
result = await self.session.execute(
    insert(FileModel)
    .values(id=uuid.uuid4(), order_id=order_id, s3_file_key=s3_key, status=FileStatus.PENDING)
    .returning(FileModel)
)
file_record = result.scalar_one()
await self.session.commit()

# 4. Публикуем в Kafka — consumer загрузит в S3
await publish_s3_upload(self.kafka_producer, StorageTopics.ORDER_FILE_UPLOAD, ...)

# 5. Возвращаем DTO с status=PENDING — клиент поллит
return FileDTO.model_validate(file_record)
```

### Типичные зависимости UseCase

| Зависимость | Когда нужна |
|-------------|-------------|
| `AsyncSession` | Всегда (чтение/запись в БД) |
| `KafkaProducerWrapper` | Когда нужна async операция с S3/внешним сервисом |
| `S3Client` | Только для генерации presigned URL (чтение ссылок) |
| `Settings` | Конфигурационные параметры |
