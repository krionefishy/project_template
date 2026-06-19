# S3 Storage

## Поддерживаемые провайдеры

- Yandex Cloud Object Storage
- Cloud.ru (бывший SberCloud) — `tenant_id:key_id` формат ключа
- AWS S3

## Паттерн работы с файлами

### Запись / удаление — ТОЛЬКО через Kafka

```
UseCase.execute()
  → ExampleFileModel(status=PENDING) → DB commit
  → publish_s3_upload(kafka_producer, topic, body=...)
  ← возврат DTO с status=PENDING

Kafka consumer (background task):
  → S3Client.put_object(key, body, content_type)
  → (опционально) DB update: status=DONE / FAILED
```

### Чтение — presigned URL (синхронно)

```python
url = s3_client.generate_presigned_url(key, expires_in=3600)
```

## S3 ключи

- Генерировать через `Model.generate_s3_key()` — classmethod на ORM модели
- Формат: `<entity>/<entity_id>/<uuid>/<sanitized_filename>`
- Использовать `sanitize_key_segment()` для безопасных имён

## Локальная конфигурация (config.yaml)

```yaml
s3:
  endpoint_url: "https://storage.yandexcloud.net"
  key_id: "your-key-id"
  secret_key: "your-secret"
  bucket_name: "your-bucket"
  region: "ru-central-1"
  tenant_id: ""   # заполнить для Yandex Cloud / Cloud.ru
  verify: true
```
