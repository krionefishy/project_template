# Tests

## Структура

Тесты зеркалируют структуру `backend/app/`:

```
tests/
├── conftest.py           # Глобальные фикстуры
├── builder.py            # Builder для тестовых данных
├── mocks/
│   ├── broker.py         # FakeKafkaBroker
│   └── storage.py        # MockS3Client
├── example_domain/
│   ├── test_api_get_example.py
│   ├── test_api_create_example.py
│   └── test_upload_example_file_usecase.py
└── auth/
    ├── test_api_login.py
    └── test_refresh_token_usecase.py
```

## Изоляция тестов (SAVEPOINT паттерн)

Каждый тест выполняется внутри SAVEPOINT-транзакции, которая откатывается по окончании.  
Таблицы создаются один раз (session-scope), данные не накапливаются между тестами.

## Builder паттерн

Вместо статических фикстур-данных используем Builder:

```python
# ❌ Не так
@pytest.fixture
def existing_example():
    return {"id": "...", "title": "Test"}

# ✅ Вот так
async def test_something(builder: Builder):
    example = await builder.build_example(title="Test", status=ExampleStatus.ACTIVE)
    # используем example.id, example.title и т.д.
```

## Именование тестов

```
test_returns_200_when_user_gets_existing_example
test_returns_404_when_example_not_found
test_returns_202_when_file_queued_for_upload
test_returns_403_when_user_lacks_permission
```

## Запуск

```bash
just test               # все тесты
just test-cov           # с coverage
just test-smoke         # только @pytest.mark.smoke
just test-file tests/example_domain/test_api_get_example.py
```

## Правила

- Нет реальных вызовов Kafka в тестах — `FakeKafkaBroker`
- Нет реальных вызовов S3 в тестах — `MockS3Client`
- Нет реального Redis в тестах — `NoopRedis`
- Тесты API работают через `httpx.AsyncClient` (ASGI transport)
- Один test file = один endpoint или один UseCase
- Группировка в классы по сценарию: `class TestGetExample:`
