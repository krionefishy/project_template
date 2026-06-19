# Mocks

## Назначение

Фейковые реализации внешних сервисов для тестов.  
Никаких реальных сетевых вызовов в тестах.

## `FakeKafkaBroker`

Заменяет `KafkaProducerWrapper`. Хранит все отправленные сообщения в памяти.

```python
async def test_file_upload_queues_kafka_message(client, mock_kafka_broker):
    mock_kafka_broker.clear()
    await client.post("/api/v1/examples/1/files", ...)
    messages = mock_kafka_broker.get_messages("storage.s3.example.upload")
    assert len(messages) == 1
    assert messages[0]["payload"]["key"].startswith("examples/")
```

## `MockS3Client`

Заменяет `S3Client`. Хранит "загруженные" файлы в `dict`.

```python
async def test_s3_upload_success(mock_s3_client):
    await mock_s3_client.put_object("my/key", b"data", "text/plain")
    assert await mock_s3_client.object_exists("my/key")
    assert mock_s3_client.get_object("my/key") == b"data"
```

## Как добавить новый mock

1. Создать класс-наследник реального клиента
2. Переопределить все async методы, которые делают сетевые вызовы
3. Хранить состояние в `dict` или `list`
4. Добавить fixture в `conftest.py` с нужным scope
