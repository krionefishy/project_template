# Kafka Streams

## Назначение

Все "тяжёлые" операции с внешними сервисами (S3, email, платёжные системы) делаются **асинхронно через Kafka**:

```
API (запрос)
  → UseCase: записать в БД status=PENDING + publish_s3_upload()
  → Kafka consumer: забрать событие → загрузить в S3
  → Consumer: обновить статус DONE / FAILED
```

HTTP-ответ отправляется сразу после шага 2 (не ждёт S3).

## Структура

| Файл | Назначение |
|------|------------|
| `producer.py` | `KafkaProducerWrapper` — отправка событий |
| `consumer.py` | `@kafka_subscriber` декоратор + `start_consumers()` |
| `topics.py` | Все топики как константы. Нигде не используем "сырые" строки |
| `storage_events.py` | `S3UploadEvent`, `S3DeleteEvent` + хелперы `publish_s3_upload/delete()` |
| `subscribers/s3.py` | Конкретные consumer-хэндлеры для S3 операций |

## Как добавить consumer для нового файлового типа

1. Добавить топик в `topics.py`:

```python
class StorageTopics:
    MY_ENTITY_UPLOAD = "storage.s3.my_entity.upload"
    MY_ENTITY_DELETE = "storage.s3.my_entity.delete"
```

2. Зарегистрировать топик в `S3_CONSUMER_TOPICS`:

```python
S3_CONSUMER_TOPICS = [
    ...
    StorageTopics.MY_ENTITY_UPLOAD,
    StorageTopics.MY_ENTITY_DELETE,
]
```

3. Создать handler в `subscribers/s3.py` или новом файле:

```python
@kafka_subscriber(StorageTopics.MY_ENTITY_UPLOAD)
async def run_my_entity_upload_consumer(s3_client: S3Client, payload: dict) -> None:
    event = S3UploadEvent(**payload)
    body = base64.b64decode(event.content_base64)
    await s3_client.put_object(event.key, body, event.content_type, event.metadata)
```

4. Импортировать модуль в `subscribers/__init__.py`

5. В UseCase вызвать `publish_s3_upload(kafka_producer, StorageTopics.MY_ENTITY_UPLOAD, ...)`

## Паттерн ретрая

Consumer при ошибке логирует и ожидает `retry_backoff_ms` перед следующей попыткой.  
Для critical операций — добавить DLQ (Dead Letter Queue) топик.
